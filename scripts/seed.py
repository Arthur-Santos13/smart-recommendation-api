"""
Seed runner — populates the database with realistic fake data.

Behaviour patterns per persona
────────────────────────────────────────────────────────────────────────────
tech_enthusiast  → strong affinity for technology + science items
                   high completion rate (reads thoroughly)
business_analyst → strong affinity for business + education items
                   mix of views and completions, occasional clicks on tech
health_seeker    → strong affinity for health + general items
                   moderate engagement, many views few completions
generalist       → interacts across all categories
                   lower per-category depth, broader coverage

Event probability tables (per persona × category)
────────────────────────────────────────────────────────────────────────────
Each tuple: (p_view, p_click, p_complete)  — independent roll per event type
"""

import random
import sys
from pathlib import Path

# Make sure the project root is on sys.path when run directly
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.item import ItemCategory
from app.models.user import User
from app.models.user_event import EventType, UserEvent
from app.repositories.item_repository import ItemRepository
from app.repositories.user_event_repository import UserEventRepository
from app.repositories.user_repository import UserRepository
from scripts.seed_data import ITEMS, USERS

# ---------------------------------------------------------------------------
# Interaction probability tables
# (p_view, p_click, p_complete)
# ---------------------------------------------------------------------------
PERSONA_PREFS: dict[str, dict[str, tuple[float, float, float]]] = {
    "tech_enthusiast": {
        ItemCategory.TECHNOLOGY: (0.95, 0.80, 0.70),
        ItemCategory.SCIENCE:    (0.80, 0.60, 0.50),
        ItemCategory.BUSINESS:   (0.30, 0.15, 0.10),
        ItemCategory.HEALTH:     (0.20, 0.10, 0.05),
        ItemCategory.EDUCATION:  (0.40, 0.25, 0.20),
        ItemCategory.GENERAL:    (0.35, 0.20, 0.15),
    },
    "business_analyst": {
        ItemCategory.TECHNOLOGY: (0.40, 0.25, 0.15),
        ItemCategory.SCIENCE:    (0.30, 0.15, 0.10),
        ItemCategory.BUSINESS:   (0.95, 0.80, 0.70),
        ItemCategory.HEALTH:     (0.25, 0.10, 0.05),
        ItemCategory.EDUCATION:  (0.75, 0.55, 0.45),
        ItemCategory.GENERAL:    (0.40, 0.25, 0.20),
    },
    "health_seeker": {
        ItemCategory.TECHNOLOGY: (0.20, 0.10, 0.05),
        ItemCategory.SCIENCE:    (0.35, 0.20, 0.10),
        ItemCategory.BUSINESS:   (0.25, 0.10, 0.05),
        ItemCategory.HEALTH:     (0.95, 0.75, 0.55),
        ItemCategory.EDUCATION:  (0.40, 0.20, 0.15),
        ItemCategory.GENERAL:    (0.70, 0.50, 0.35),
    },
    "generalist": {
        ItemCategory.TECHNOLOGY: (0.55, 0.35, 0.25),
        ItemCategory.SCIENCE:    (0.55, 0.35, 0.25),
        ItemCategory.BUSINESS:   (0.55, 0.35, 0.25),
        ItemCategory.HEALTH:     (0.55, 0.35, 0.25),
        ItemCategory.EDUCATION:  (0.55, 0.35, 0.25),
        ItemCategory.GENERAL:    (0.55, 0.35, 0.25),
    },
}

EVENT_WEIGHTS: dict[str, int] = {
    EventType.VIEW: 1,
    EventType.CLICK: 2,
    EventType.COMPLETE: 3,
}


def _seed_users(db: Session, repo: UserRepository) -> dict[str, tuple[User, str]]:
    """Insert users and return {email: (User, persona)}."""
    result: dict[str, tuple[User, str]] = {}
    for name, email, persona in USERS:
        existing = repo.get_by_email(email)
        if existing:
            print(f"  [skip] user already exists: {email}")
            result[email] = (existing, persona)
        else:
            user = repo.create(name=name, email=email)
            print(f"  [+] user: {email} ({persona})")
            result[email] = (user, persona)
    return result


def _seed_items(db: Session, repo: ItemRepository) -> list:
    """Insert items and return ORM list."""
    items = []
    for title, category, tags, description in ITEMS:
        total, existing = repo.list_items(category=None, page=1, limit=1000)
        match = next((i for i in existing if i.title == title), None)
        if match:
            print(f"  [skip] item already exists: {title[:50]}")
            items.append(match)
        else:
            item = repo.create(
                title=title,
                category=category.value,
                tags=tags,
                description=description,
            )
            print(f"  [+] item: {title[:50]} [{category.value}]")
            items.append(item)
    return items


def _seed_events(
    event_repo: UserEventRepository,
    users_map: dict[str, tuple[User, str]],
    items: list,
    rng: random.Random,
) -> int:
    """Generate interaction events based on persona probability tables."""
    total = 0
    for _email, (user, persona) in users_map.items():
        prefs = PERSONA_PREFS[persona]
        for item in items:
            category = ItemCategory(item.category)
            p_view, p_click, p_complete = prefs[category]

            # Each event type is an independent probabilistic roll.
            # A completion implies the user also viewed and clicked it, so
            # we maintain logical ordering without strictly enforcing dependency.
            if rng.random() < p_view:
                existing = event_repo.get_existing(user.id, item.id, EventType.VIEW)
                if not existing:
                    event_repo.create(
                        user_id=user.id,
                        item_id=item.id,
                        event_type=EventType.VIEW,
                        weight=EVENT_WEIGHTS[EventType.VIEW],
                    )
                    total += 1

            if rng.random() < p_click:
                existing = event_repo.get_existing(user.id, item.id, EventType.CLICK)
                if not existing:
                    event_repo.create(
                        user_id=user.id,
                        item_id=item.id,
                        event_type=EventType.CLICK,
                        weight=EVENT_WEIGHTS[EventType.CLICK],
                    )
                    total += 1

            if rng.random() < p_complete:
                existing = event_repo.get_existing(user.id, item.id, EventType.COMPLETE)
                if not existing:
                    event_repo.create(
                        user_id=user.id,
                        item_id=item.id,
                        event_type=EventType.COMPLETE,
                        weight=EVENT_WEIGHTS[EventType.COMPLETE],
                    )
                    total += 1

    return total


def run_seed(seed: int = 42) -> None:
    rng = random.Random(seed)
    db: Session = SessionLocal()
    try:
        user_repo = UserRepository(db)
        item_repo = ItemRepository(db)
        event_repo = UserEventRepository(db)

        print("\n── Seeding users ──────────────────────────────")
        users_map = _seed_users(db, user_repo)

        print("\n── Seeding items ──────────────────────────────")
        items = _seed_items(db, item_repo)

        print("\n── Generating interaction events ──────────────")
        total_events = _seed_events(event_repo, users_map, items, rng)

        print(
            f"\n✓ Seed complete — "
            f"{len(users_map)} users | {len(items)} items | {total_events} new events\n"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
