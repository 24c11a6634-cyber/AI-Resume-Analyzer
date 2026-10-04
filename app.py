from flask import Flask, render_template, request
from pypdf import PdfReader
from werkzeug.utils import secure_filename
import os
import re


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# SKILL DATABASE
# ============================================================

SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",

    "html",
    "html5",
    "css",
    "css3",
    "react",
    "react.js",
    "angular",
    "angular.js",
    "node.js",

    "sql",
    "mysql",
    "mongodb",
    "postgresql",

    "flask",
    "django",

    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data science",

    "pandas",
    "numpy",
    "tensorflow",
    "pytorch",

    "git",
    "github",
    "docker",
    "aws",

    "webpack",
    "bootstrap",
    "jquery",
    "sass",
    "less",
    "figma",
    "photoshop",
    "illustrator",
    "jira",
    "gulp",
    "grunt",
    "foundation",
    "material ui",
    "zeplin",

    "rest api",
    "api",
    "problem solving",
    "communication",
    "seo"
]


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "reactjs": "react",
    "react js": "react",
    "react.js": "react",

    "angularjs": "angular",
    "angular js": "angular",
    "angular.js": "angular",

    "nodejs": "node.js",
    "node js": "node.js",

    "javascript": "javascript",
    "java script": "javascript",

    "typescript": "typescript",

    "html5": "html5",
    "html 5": "html5",

    "css3": "css3",
    "css 3": "css3",

    "c plus plus": "c++",

    "restful api": "rest api",
    "rest apis": "rest api",
    "rest api": "rest api",

    "git hub": "github",

    "machine-learning": "machine learning",
    "machine learning": "machine learning",

    "deep-learning": "deep learning",
    "deep learning": "deep learning",

    "artificial-intelligence": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",

    "problem-solving": "problem solving"
}


# ============================================================
# JOB ROLE DATABASE
# ============================================================

ROLE_GROUPS = {
    "Frontend Developer": {
        "skills": [
            "html",
            "html5",
            "css",
            "css3",
            "javascript",
            "react",
            "angular",
            "bootstrap"
        ],
        "aliases": [
            "frontend developer",
            "front end developer",
            "front-end developer",
            "frontend engineer",
            "front end engineer"
        ]
    },

    "React Developer": {
        "skills": [
            "react",
            "javascript",
            "html",
            "css",
            "webpack",
            "git"
        ],
        "aliases": [
            "react developer",
            "react engineer",
            "react.js developer",
            "react js developer"
        ]
    },

    "Web Developer": {
        "skills": [
            "html",
            "html5",
            "css",
            "css3",
            "javascript",
            "react",
            "angular",
            "bootstrap",
            "jquery"
        ],
        "aliases": [
            "web developer",
            "web engineer",
            "web development"
        ]
    },

    "UI Developer": {
        "skills": [
            "html",
            "html5",
            "css",
            "css3",
            "javascript",
            "bootstrap",
            "jquery",
            "sass",
            "less",
            "figma"
        ],
        "aliases": [
            "ui developer",
            "ui engineer",
            "user interface developer"
        ]
    },

    "Java Developer": {
        "skills": [
            "java",
            "spring",
            "sql",
            "mysql"
        ],
        "aliases": [
            "java developer",
            "java engineer"
        ]
    },

    "Python Developer": {
        "skills": [
            "python",
            "flask",
            "django",
            "sql",
            "pandas",
            "numpy"
        ],
        "aliases": [
            "python developer",
            "python engineer"
        ]
    },

    "Data Analyst": {
        "skills": [
            "python",
            "sql",
            "pandas",
            "numpy",
            "data science"
        ],
        "aliases": [
            "data analyst",
            "data analytics",
            "analytics"
        ]
    },

    "ML Engineer": {
        "skills": [
            "python",
            "machine learning",
            "deep learning",
            "pandas",
            "numpy",
            "tensorflow",
            "pytorch"
        ],
        "aliases": [
            "machine learning engineer",
            "ml engineer",
            "machine learning developer"
        ]
    },

    "AI Engineer": {
        "skills": [
            "python",
            "machine learning",
            "deep learning",
            "artificial intelligence",
            "tensorflow",
            "pytorch"
        ],
        "aliases": [
            "ai engineer",
            "ai developer",
            "artificial intelligence engineer"
        ]
    }
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def allowed_file(filename):
    """Check whether uploaded file is a supported PDF."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def normalize_text(text):
    """
    Normalize resume/JD text while preserving useful technical
    terms such as C++, Node.js, React.js, HTML5 and CSS3.
    """
    text = text.lower()

    replacements = {
        "react js": "react.js",
        "reactjs": "react.js",

        "angular js": "angular.js",
        "angularjs": "angular.js",

        "node js": "node.js",
        "nodejs": "node.js",

        "html 5": "html5",
        "css 3": "css3",

        "restful api": "rest api",
        "rest apis": "rest api",

        "git hub": "github",

        "c plus plus": "c++",

        "problem-solving": "problem solving"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return re.sub(r"\s+", " ", text).strip()


def contains_skill(text, skill):
    """
    Safer skill matching to reduce false positives.
    """
    text = normalize_text(text)

    skill = skill.lower()

    if skill == "c":
        return bool(re.search(r"(?<![a-z])c(?![a-z+#])", text))

    if skill == "c++":
        return "c++" in text

    escaped = re.escape(skill)

    return bool(re.search(
        rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
        text
    ))


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text):
    """
    Detect skills from resume text.
    Returns canonical skill names.
    """

    normalized = normalize_text(text)

    found = set()

    for skill in SKILLS:

        if contains_skill(normalized, skill):
            canonical = SKILL_ALIASES.get(skill, skill)
            found.add(canonical)

    # Additional alias detection
    for alias, canonical in SKILL_ALIASES.items():
        if contains_skill(normalized, alias):
            found.add(canonical)

    # HTML5/CSS3 also imply the base technologies
    if "html5" in found:
        found.add("html")

    if "css3" in found:
        found.add("css")

    return sorted(found)


# ============================================================
# EXPERIENCE DETECTION
# ============================================================

def extract_experience(text):
    """
    Detect professional experience.

    Total/general experience phrases are prioritized over
    specialized experience phrases.

    Example:
    "10+ years of expertise and 6 years specialized experience"

    -> Returns 10 years.
    """

    normalized = normalize_text(text)

    # --------------------------------------------------------
    # First look for explicit total/general experience
    # --------------------------------------------------------

    total_patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+expertise",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+professional\s+expertise",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+experience",
        r"experience\s+of\s+(\d+(?:\.\d+)?)\s*\+?\s*years?",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+in\s+(?:software|web|it|technology)",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+work\s+experience"
    ]

    total_experiences = []

    for pattern in total_patterns:
        matches = re.findall(pattern, normalized)

        for value in matches:
            try:
                total_experiences.append(float(value))
            except ValueError:
                continue

    # If multiple general experience values exist,
    # use the largest one because it is most likely the
    # overall professional experience.
    if total_experiences:
        return max(total_experiences)

    # --------------------------------------------------------
    # Look for work-history date ranges
    # --------------------------------------------------------

    year_ranges = re.findall(
        r"\b(19\d{2}|20\d{2})\s*[-–]\s*(present|current|19\d{2}|20\d{2})\b",
        normalized
    )

    if year_ranges:
        years = []

        for start, end in year_ranges:
            try:
                start_year = int(start)

                if end in ("present", "current"):
                    end_year = 2026
                else:
                    end_year = int(end)

                if end_year >= start_year:
                    years.append(end_year - start_year)

            except ValueError:
                continue

        if years:
            return float(max(years))

    # --------------------------------------------------------
    # Generic fresher detection
    # --------------------------------------------------------

    fresher_words = [
        "fresher",
        "recent graduate",
        "recently graduated",
        "no experience"
    ]

    if any(word in normalized for word in fresher_words):
        return 0.0

    return 0.0


def format_experience(years):
    """Format experience for display."""

    if years == 0:
        return "Fresher"

    if float(years).is_integer():
        return f"{int(years)} years"

    return f"{years:.1f} years"


# ============================================================
# ROLE MATCHING
# ============================================================

def calculate_role_scores(found_skills, resume_text):
    """
    Calculate role compatibility using both explicit role
    mentions and technical skill coverage.
    """

    normalized = normalize_text(resume_text)
    found = set(found_skills)

    scores = {}

    for role, data in ROLE_GROUPS.items():

        role_skills = set(data["skills"])

        matched = found.intersection(role_skills)

        skill_score = (
            len(matched) / len(role_skills) * 100
            if role_skills
            else 0
        )

        explicit_role = any(
            alias in normalized
            for alias in data["aliases"]
        )

        if explicit_role:
            score = max(skill_score, 100)
        else:
            score = skill_score

        scores[role] = round(min(score, 100))

    return scores


def detect_resume_roles(resume_text, role_scores):
    """
    Detect roles actually supported by the resume.

    Only return roles with strong evidence.
    """

    normalized = normalize_text(resume_text)

    detected = []

    for role, data in ROLE_GROUPS.items():

        explicit = any(
            alias in normalized
            for alias in data["aliases"]
        )

        score = role_scores.get(role, 0)

        if explicit or score >= 70:
            detected.append(role)

    return detected


# ============================================================
# JOB DESCRIPTION ANALYSIS
# ============================================================

def classify_job_skills(job_description):
    """
    Split JD skills into required and preferred groups.

    The function also handles JDs where explicit
    Required/Preferred headings are not present.
    """

    text = normalize_text(job_description)

    required = set()
    preferred = set()

    # --------------------------------------------------------
    # Extract preferred section
    # --------------------------------------------------------

    preferred_patterns = [
        r"preferred skills?:?(.*?)(?=education|qualifications|responsibilities|requirements|$)",
        r"nice to have:?(.*?)(?=education|qualifications|responsibilities|requirements|$)",
        r"good to have:?(.*?)(?=education|qualifications|responsibilities|requirements|$)"
    ]

    preferred_section = ""

    for pattern in preferred_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            preferred_section += " " + match.group(1)

    # --------------------------------------------------------
    # Extract required section
    # --------------------------------------------------------

    required_patterns = [
        r"required skills?:?(.*?)(?=preferred skills?|nice to have|good to have|education|$)",
        r"requirements?:?(.*?)(?=preferred skills?|nice to have|good to have|education|$)",
        r"qualifications?:?(.*?)(?=preferred skills?|nice to have|good to have|education|$)"
    ]

    required_section = ""

    for pattern in required_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            required_section += " " + match.group(1)

    # --------------------------------------------------------
    # Extract skills from sections
    # --------------------------------------------------------

    for skill in SKILLS:

        if contains_skill(preferred_section, skill):
            preferred.add(SKILL_ALIASES.get(skill, skill))

        if contains_skill(required_section, skill):
            required.add(SKILL_ALIASES.get(skill, skill))

    # --------------------------------------------------------
    # If explicit sections don't exist, infer requirements
    # --------------------------------------------------------

    if not required:
        responsibility_text = text

        for skill in SKILLS:
            if contains_skill(responsibility_text, skill):
                required.add(SKILL_ALIASES.get(skill, skill))

    # Remove preferred skills from required
    required -= preferred

    return sorted(required), sorted(preferred)


# ============================================================
# JOB ROLE DETECTION
# ============================================================

def detect_job_role(job_description, required_skills, preferred_skills):
    """
    Identify the most likely role from the job title and
    technical skills.
    """

    normalized = normalize_text(job_description)

    # Explicit role title has highest priority
    for role, data in ROLE_GROUPS.items():

        for alias in data["aliases"]:

            if alias in normalized:
                return role

    # Otherwise calculate role from skills
    all_jd_skills = set(required_skills + preferred_skills)

    if not all_jd_skills:
        return "General Technical Role"

    best_role = "General Technical Role"
    best_score = 0

    for role, data in ROLE_GROUPS.items():

        role_skills = set(data["skills"])

        overlap = len(
            all_jd_skills.intersection(role_skills)
        )

        if overlap > best_score:
            best_score = overlap
            best_role = role

    return best_role


# ============================================================
# JOB SKILL MATCH
# ============================================================

def calculate_skill_match(found_skills, target_skills):
    """
    Calculate percentage match between resume skills
    and target skills.
    """

    target = set(target_skills)

    if not target:
        return 100, [], []

    found = set(found_skills)

    matched = sorted(found.intersection(target))
    missing = sorted(target - found)

    score = round(
        len(matched) / len(target) * 100
    )

    return score, matched, missing


# ============================================================
# KEYWORD MATCH
# ============================================================

def calculate_keyword_match(resume_text, job_description):
    """
    Estimate general keyword similarity between resume
    and job description.
    """

    resume = normalize_text(resume_text)
    jd = normalize_text(job_description)

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9+#.-]{2,}\b",
        jd
    )

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "are",
        "you",
        "our",
        "your",
        "will",
        "have",
        "has",
        "from",
        "into",
        "using",
        "work",
        "working",
        "experience",
        "years",
        "good",
        "strong",
        "knowledge"
    }

    meaningful_words = [
        word.lower()
        for word in words
        if word.lower() not in stop_words
    ]

    if not meaningful_words:
        return 0

    matched = sum(
        1
        for word in meaningful_words
        if word in resume
    )

    score = round(
        matched / len(meaningful_words) * 100
    )

    return min(score, 100)


# ============================================================
# OVERALL JOB MATCH
# ============================================================

def calculate_job_match(
    required_score,
    preferred_score,
    experience_score,
    role_score,
    keyword_score
):
    """
    Calculate final job-description match.

    Main formula:
    Skills       60%
    Experience   15%
    Role         15%
    Keywords     10%

    Skill component:
    Required 70%
    Preferred 30%
    """

    skill_component = (
        required_score * 0.70
        + preferred_score * 0.30
    )

    overall = (
        skill_component * 0.60
        + experience_score * 0.15
        + role_score * 0.15
        + keyword_score * 0.10
    )

    return round(min(overall, 100))


def match_label(score):
    """Return a readable match category."""

    if score >= 85:
        return "Excellent Match"

    if score >= 70:
        return "Strong Match"

    if score >= 55:
        return "Moderate Match"

    if score >= 40:
        return "Needs Improvement"

    return "Low Match"


# ============================================================
# EXPERIENCE MATCH
# ============================================================

def calculate_experience_match(
    resume_experience,
    job_description
):
    """
    Detect required years from the job description.
    """

    normalized = normalize_text(job_description)

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+experience",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+experience",
        r"experience\s+of\s+(\d+(?:\.\d+)?)\s*\+?\s*years?"
    ]

    required_years = 0.0

    for pattern in patterns:
        match = re.search(pattern, normalized)

        if match:
            try:
                required_years = float(match.group(1))
                break
            except ValueError:
                pass

    if required_years == 0:
        return 100, 0

    if resume_experience >= required_years:
        score = 100
    else:
        score = round(
            resume_experience / required_years * 100
        )

    return min(score, 100), required_years


# ============================================================
# RESUME STRENGTHS
# ============================================================

def generate_strengths(
    found_skills,
    experience,
    role_scores
):
    strengths = []

    if len(found_skills) >= 8:
        strengths.append(
            "Good technical skill coverage"
        )

    frontend_skills = {
        "html",
        "html5",
        "css",
        "css3",
        "javascript",
        "react",
        "angular"
    }

    if len(
        set(found_skills).intersection(frontend_skills)
    ) >= 3:
        strengths.append(
            "Strong web development foundation"
        )

    programming = {
        "python",
        "java",
        "javascript",
        "c",
        "c++"
    }

    if set(found_skills).intersection(programming):
        strengths.append(
            "Programming language knowledge"
        )

    if "git" in found_skills or "github" in found_skills:
        strengths.append(
            "Version control knowledge"
        )

    if experience > 0:
        strengths.append(
            "Professional experience detected"
        )

    best_role_score = (
        max(role_scores.values())
        if role_scores
        else 0
    )

    if best_role_score >= 80:
        strengths.append(
            "Strong alignment with a specific job role"
        )

    if not strengths:
        strengths.append(
            "Resume contains a useful technical foundation"
        )

    return strengths


# ============================================================
# IMPROVEMENTS
# ============================================================

def generate_improvements(found_skills, role_scores):

    improvements = []

    found = set(found_skills)

    if "python" not in found:
        improvements.append(
            "Consider adding Python"
        )

    if "sql" not in found and "mysql" not in found:
        improvements.append(
            "Consider adding SQL/database skills"
        )

    if not (
        "machine learning" in found
        or "artificial intelligence" in found
        or "deep learning" in found
    ):
        improvements.append(
            "Add AI or Machine Learning skills for AI-related roles"
        )

    if "github" not in found:
        improvements.append(
            "Add GitHub projects or repositories"
        )

    if "rest api" not in found:
        improvements.append(
            "Consider adding REST API experience"
        )

    if "typescript" not in found:
        improvements.append(
            "Consider adding TypeScript for modern frontend roles"
        )

    if not improvements:
        improvements.append(
            "Continue strengthening projects and measurable achievements"
        )

    return improvements[:6]


# ============================================================
# ATS SCORE
# ============================================================

def calculate_ats_score(
    text,
    found_skills,
    experience,
    role_scores
):
    """
    Estimate ATS readiness.

    Factors:
    - Skill coverage
    - Experience
    - Resume length/content
    - Role alignment
    """

    normalized = normalize_text(text)

    skill_points = min(len(found_skills) * 3, 30)

    experience_points = 20 if experience > 0 else 5

    content_points = 0

    important_sections = [
        "experience",
        "education",
        "skills",
        "project",
        "summary"
    ]

    for section in important_sections:
        if section in normalized:
            content_points += 6

    content_points = min(content_points, 30)

    role_points = 20 if (
        role_scores
        and max(role_scores.values()) >= 70
    ) else 10

    score = (
        skill_points
        + experience_points
        + content_points
        + role_points
    )

    return min(round(score), 100)


# ============================================================
# SKILL CATEGORIES
# ============================================================

def categorize_skills(found_skills):

    programming = []
    frontend = []
    backend = []
    data_ai = []
    tools = []
    other = []

    programming_skills = {
        "python",
        "java",
        "javascript",
        "c",
        "c++",
        "typescript"
    }

    frontend_skills = {
        "html",
        "html5",
        "css",
        "css3",
        "react",
        "angular",
        "angular.js",
        "bootstrap",
        "jquery",
        "sass",
        "less",
        "foundation",
        "material ui"
    }

    backend_skills = {
        "node.js",
        "flask",
        "django",
        "sql",
        "mysql",
        "mongodb",
        "postgresql",
        "rest api",
        "api"
    }

    data_ai_skills = {
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "data science",
        "pandas",
        "numpy",
        "tensorflow",
        "pytorch"
    }

    tool_skills = {
        "git",
        "github",
        "docker",
        "aws",
        "webpack",
        "figma",
        "photoshop",
        "illustrator",
        "jira",
        "gulp",
        "grunt",
        "zeplin"
    }

    for skill in found_skills:

        if skill in programming_skills:
            programming.append(skill)

        elif skill in frontend_skills:
            frontend.append(skill)

        elif skill in backend_skills:
            backend.append(skill)

        elif skill in data_ai_skills:
            data_ai.append(skill)

        elif skill in tool_skills:
            tools.append(skill)

        else:
            other.append(skill)

    return {
        "Programming": programming,
        "Frontend": frontend,
        "Backend": backend,
        "Data & AI": data_ai,
        "Tools": tools,
        "Other": other
    }


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(filepath):

    text = ""

    try:
        reader = PdfReader(filepath)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as error:
        print("PDF extraction error:", error)

    return text.strip()


# ============================================================
# MAIN RESUME ANALYSIS
# ============================================================

def analyze_resume(text):

    found_skills = extract_skills(text)

    experience = extract_experience(text)

    role_scores = calculate_role_scores(
        found_skills,
        text
    )

    resume_roles = detect_resume_roles(
        text,
        role_scores
    )

    ats_score = calculate_ats_score(
        text,
        found_skills,
        experience,
        role_scores
    )

    skill_score = min(
        round(len(found_skills) / 25 * 100),
        100
    )

    strengths = generate_strengths(
        found_skills,
        experience,
        role_scores
    )

    improvements = generate_improvements(
        found_skills,
        role_scores
    )

    recommended_roles = sorted(
        role_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    skills_to_add = []

    if "python" not in found_skills:
        skills_to_add.append("Python")

    if "sql" not in found_skills:
        skills_to_add.append("SQL")

    if (
        "machine learning" not in found_skills
        and "artificial intelligence" not in found_skills
    ):
        skills_to_add.append("Machine Learning")

    if "github" not in found_skills:
        skills_to_add.append("GitHub")

    return {
        "found_skills": found_skills,
        "skill_categories": categorize_skills(found_skills),
        "skill_score": skill_score,
        "ats_score": ats_score,
        "experience": experience,
        "experience_display": format_experience(experience),
        "strengths": strengths,
        "improvements": improvements,
        "skills_to_add": skills_to_add,
        "recommended_roles": recommended_roles,
        "resume_roles": resume_roles
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def file_too_large(error):
    return """
    <h2>File too large</h2>
    <p>Please upload a PDF smaller than 10 MB.</p>
    <p><a href="/">Go back</a></p>
    """, 413


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# ============================================================
# ANALYZE RESUME
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    if "resume" not in request.files:
        return """
        <h2>No resume uploaded</h2>
        <p>Please select a PDF resume.</p>
        <p><a href="/">Go back</a></p>
        """

    file = request.files["resume"]

    if file.filename == "":
        return """
        <h2>No file selected</h2>
        <p>Please select a PDF resume.</p>
        <p><a href="/">Go back</a></p>
        """

    if not allowed_file(file.filename):
        return """
        <h2>Invalid file type</h2>
        <p>Please upload a PDF file.</p>
        <p><a href="/">Go back</a></p>
        """

    filename = secure_filename(file.filename)

    if not filename:
        return """
        <h2>Invalid filename</h2>
        <p>Please upload a valid PDF file.</p>
        <p><a href="/">Go back</a></p>
        """

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    try:
        file.save(filepath)

        resume_text = extract_text_from_pdf(filepath)

        if not resume_text:
            return """
            <h2>Could not read the resume</h2>
            <p>
                The PDF may be image-based or contain text that
                cannot be extracted.
            </p>
            <p><a href="/">Go back</a></p>
            """

        result = analyze_resume(resume_text)

        # ----------------------------------------------------
        # Job Description Match
        # ----------------------------------------------------

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        job_match = None

        if job_description:

            required_skills, preferred_skills = (
                classify_job_skills(job_description)
            )

            detected_job_role = detect_job_role(
                job_description,
                required_skills,
                preferred_skills
            )

            required_score, required_matched, required_missing = (
                calculate_skill_match(
                    result["found_skills"],
                    required_skills
                )
            )

            preferred_score, preferred_matched, preferred_missing = (
                calculate_skill_match(
                    result["found_skills"],
                    preferred_skills
                )
            )

            experience_score, required_experience = (
                calculate_experience_match(
                    result["experience"],
                    job_description
                )
            )

            role_scores = result["recommended_roles"]

            role_match = 0

            for role, score in role_scores:
                if role == detected_job_role:
                    role_match = score
                    break

            keyword_score = calculate_keyword_match(
                resume_text,
                job_description
            )

            overall_score = calculate_job_match(
                required_score,
                preferred_score,
                experience_score,
                role_match,
                keyword_score
            )

            all_jd_skills = set(
                required_skills + preferred_skills
            )

            other_skills = sorted(
                set(result["found_skills"]) - all_jd_skills
            )

            job_match = {
                "score": overall_score,
                "label": match_label(overall_score),

                "detected_job_role": detected_job_role,

                "required_skills": required_skills,
                "required_matched": required_matched,
                "required_missing": required_missing,
                "required_score": required_score,

                "preferred_skills": preferred_skills,
                "preferred_matched": preferred_matched,
                "preferred_missing": preferred_missing,
                "preferred_score": preferred_score,

                "other_skills": other_skills,

                "required_experience": required_experience,
                "experience_score": experience_score,

                "role_match": role_match,
                "keyword_score": keyword_score,

                "resume_roles": result["resume_roles"]
            }

        # ----------------------------------------------------
        # HTML REPORT
        # ----------------------------------------------------

        return render_template(
            "index.html",
            result=result,
            job_match=job_match,
            analyzed=True
        )

    except Exception as error:

        print("Analysis error:", error)

        return """
        <h2>Something went wrong</h2>
        <p>
            The resume could not be analyzed.
            Please check the PDF and try again.
        </p>
        <p><a href="/">Go back</a></p>
        """

    finally:

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )