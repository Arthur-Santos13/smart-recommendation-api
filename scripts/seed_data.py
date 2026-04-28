"""
Static seed catalogue for users and items.

Users are grouped into personas that drive realistic interaction patterns:
  - tech_enthusiast   → prefers technology / science
  - business_analyst  → prefers business / education
  - health_seeker     → prefers health / general
  - generalist        → interacts across all categories
"""

from app.models.item import ItemCategory

# ---------------------------------------------------------------------------
# Users
# Each entry: (name, email, persona)
# ---------------------------------------------------------------------------
USERS: list[tuple[str, str, str]] = [
    # tech_enthusiast
    ("Alice Ferreira", "alice@example.com", "tech_enthusiast"),
    ("Bruno Costa", "bruno@example.com", "tech_enthusiast"),
    ("Carlos Mendes", "carlos@example.com", "tech_enthusiast"),
    # business_analyst
    ("Diana Souza", "diana@example.com", "business_analyst"),
    ("Eduardo Lima", "eduardo@example.com", "business_analyst"),
    ("Fernanda Alves", "fernanda@example.com", "business_analyst"),
    # health_seeker
    ("Gabriel Rocha", "gabriel@example.com", "health_seeker"),
    ("Helena Neves", "helena@example.com", "health_seeker"),
    ("Igor Teixeira", "igor@example.com", "health_seeker"),
    # generalist
    ("Julia Martins", "julia@example.com", "generalist"),
    ("Klaus Pinto", "klaus@example.com", "generalist"),
    ("Larissa Gomes", "larissa@example.com", "generalist"),
]

# ---------------------------------------------------------------------------
# Items
# Each entry: (title, category, tags, description)
# ---------------------------------------------------------------------------
ITEMS: list[tuple[str, str, str, str]] = [
    # --- TECHNOLOGY ---
    (
        "Introduction to Machine Learning with Python",
        ItemCategory.TECHNOLOGY,
        "python,machine-learning,scikit-learn,beginner",
        "A practical guide to building your first ML models with scikit-learn.",
    ),
    (
        "FastAPI: Building High-Performance APIs",
        ItemCategory.TECHNOLOGY,
        "python,fastapi,rest,backend",
        "Step-by-step tutorial for building production-ready APIs with FastAPI.",
    ),
    (
        "Docker for Developers",
        ItemCategory.TECHNOLOGY,
        "docker,containers,devops,deployment",
        "Learn how to containerise applications and manage multi-container environments.",
    ),
    (
        "PostgreSQL Performance Tuning",
        ItemCategory.TECHNOLOGY,
        "postgresql,database,performance,indexing",
        "Advanced techniques for optimising slow queries and index strategies.",
    ),
    (
        "Deep Learning Fundamentals",
        ItemCategory.TECHNOLOGY,
        "deep-learning,neural-networks,tensorflow,python",
        "Core concepts of deep learning applied to real-world classification tasks.",
    ),
    (
        "Kubernetes in Production",
        ItemCategory.TECHNOLOGY,
        "kubernetes,k8s,devops,orchestration",
        "Deploying and managing containerised workloads at scale with Kubernetes.",
    ),
    # --- SCIENCE ---
    (
        "Quantum Computing: A Gentle Introduction",
        ItemCategory.SCIENCE,
        "quantum,computing,physics,emerging-tech",
        "An accessible overview of quantum bits, gates and algorithms.",
    ),
    (
        "Climate Change: Data and Models",
        ItemCategory.SCIENCE,
        "climate,data-science,environment,modeling",
        "How scientists use data to model and predict climate change impacts.",
    ),
    (
        "Neuroscience and Artificial Intelligence",
        ItemCategory.SCIENCE,
        "neuroscience,AI,brain,cognition",
        "Exploring the intersection between brain research and AI architectures.",
    ),
    (
        "The Mathematics Behind Recommendation Systems",
        ItemCategory.SCIENCE,
        "math,linear-algebra,recommendations,collaborative-filtering",
        "Linear algebra and probability theory powering modern recommenders.",
    ),
    # --- BUSINESS ---
    (
        "Product-Led Growth Strategies",
        ItemCategory.BUSINESS,
        "product,growth,saas,strategy",
        "How leading SaaS companies drive acquisition through product experience.",
    ),
    (
        "Financial Modelling for Startups",
        ItemCategory.BUSINESS,
        "finance,startups,excel,modelling",
        "Build robust financial models for fundraising and operational planning.",
    ),
    (
        "Data-Driven Decision Making",
        ItemCategory.BUSINESS,
        "analytics,business-intelligence,kpi,decisions",
        "Frameworks for turning data insights into strategic business actions.",
    ),
    (
        "OKRs: Setting Goals That Work",
        ItemCategory.BUSINESS,
        "okr,goals,management,performance",
        "A practical guide to implementing OKRs across teams and organisations.",
    ),
    # --- HEALTH ---
    (
        "Evidence-Based Nutrition",
        ItemCategory.HEALTH,
        "nutrition,diet,science,wellness",
        "What the latest research actually says about optimal eating habits.",
    ),
    (
        "Mental Health in the Workplace",
        ItemCategory.HEALTH,
        "mental-health,burnout,wellness,productivity",
        "Recognising and addressing burnout, anxiety and stress at work.",
    ),
    (
        "Sleep Science and Performance",
        ItemCategory.HEALTH,
        "sleep,performance,recovery,science",
        "How quality sleep directly impacts cognitive performance and longevity.",
    ),
    (
        "Strength Training for Longevity",
        ItemCategory.HEALTH,
        "fitness,strength,longevity,exercise",
        "Science-backed resistance training principles for long-term health.",
    ),
    # --- EDUCATION ---
    (
        "How to Learn Anything Faster",
        ItemCategory.EDUCATION,
        "learning,memory,productivity,techniques",
        "Evidence-based techniques including spaced repetition and active recall.",
    ),
    (
        "Teaching with Technology",
        ItemCategory.EDUCATION,
        "edtech,teaching,tools,online-learning",
        "Integrating digital tools to enhance engagement and learning outcomes.",
    ),
    (
        "Critical Thinking in the Age of AI",
        ItemCategory.EDUCATION,
        "critical-thinking,AI,reasoning,education",
        "Developing analytical skills in a world increasingly shaped by AI.",
    ),
    # --- GENERAL ---
    (
        "The Art of Deep Work",
        ItemCategory.GENERAL,
        "productivity,focus,deep-work,habits",
        "Strategies for cultivating sustained concentration in a distracted world.",
    ),
    (
        "Stoicism for Modern Life",
        ItemCategory.GENERAL,
        "philosophy,stoicism,mindset,resilience",
        "Ancient Stoic principles applied to everyday challenges and decisions.",
    ),
    (
        "Public Speaking Mastery",
        ItemCategory.GENERAL,
        "communication,public-speaking,confidence,presentation",
        "Practical exercises to build confidence and clarity as a speaker.",
    ),
]
