#!/usr/bin/env python3
"""Generate a rich example_vault with 1000 captures, ~60 notes, ~12 topics, and a knowledge graph.

Usage:
    uv run python scripts/generate_example_vault.py
"""

from __future__ import annotations

import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import frontmatter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "example_vault"
sys.path.insert(0, str(ROOT / "src"))

from vault_mcp.adapters.local import LocalStorageAdapter
from vault_mcp.graph.clustering import compute_clusters
from vault_mcp.graph.engine import VaultGraph
from vault_mcp.utils.markdown import auto_insert_wikilinks, collect_note_titles

# ---------------------------------------------------------------------------
# Pre-written insight corpus — ~200 unique insights, ~40 per domain group
# ---------------------------------------------------------------------------

CAPTURES: list[dict] = []

def _add(domain_tags: list[str], title: str, insight: str, source: str = "conversation"):
    CAPTURES.append({"tags": domain_tags, "title": title, "insight": insight, "source": source})

# ── AI / LLM / Prompt Engineering (~45) ──────────────────────────────────

_add(["ai", "llm"], "Transformer Attention Is All You Need",
     "The transformer architecture replaced recurrence with self-attention, enabling massive parallelism during training and scaling to billions of parameters.")
_add(["ai", "llm"], "Tokenization Affects Model Performance",
     "Byte-pair encoding tokenization can split rare words awkwardly, hurting performance on domain-specific text. Custom tokenizers often help.")
_add(["ai", "llm"], "Temperature Controls Output Randomness",
     "Setting temperature to 0 makes LLM output deterministic. Higher values increase creativity but risk incoherence above 1.0.")
_add(["ai", "llm"], "Context Window Limits Shape Prompt Design",
     "Models with larger context windows can process entire documents, but cost and latency scale with input length. Chunking strategies matter.")
_add(["ai", "prompt-engineering"], "Chain of Thought Prompting Explained",
     "Asking a model to think step by step before answering improves accuracy on math and logic tasks by 20-40%.", "article")
_add(["ai", "prompt-engineering"], "System Prompts Set LLM Behavior",
     "System prompts define persona, constraints, and output format upfront. They reduce repeated instructions and improve consistency.", "article")
_add(["ai", "prompt-engineering"], "Few-Shot Examples Improve Output Quality",
     "Providing 2-3 concrete input/output examples helps models match desired format and style. Essential for structured outputs like JSON.")
_add(["ai", "llm"], "RLHF Aligns Models with Human Preferences",
     "Reinforcement learning from human feedback trains models to produce outputs humans prefer, but can introduce sycophancy if reward models are biased.")
_add(["ai", "llm"], "Mixture of Experts Reduces Compute Cost",
     "MoE architectures activate only a subset of parameters per token, achieving larger model capacity without proportional compute increase.")
_add(["ai", "programming"], "AI Pair Programming Changes Development",
     "Using AI coding assistants shifts the developer's role from writing code to reviewing and guiding code generation. Clear specifications become the key skill.")
_add(["ai", "llm"], "Embedding Models Capture Semantic Meaning",
     "Text embeddings map sentences to high-dimensional vectors where semantic similarity correlates with cosine distance. Critical for RAG systems.")
_add(["ai", "prompt-engineering"], "Structured Output Formats Reduce Parsing Errors",
     "Asking LLMs to respond in JSON or XML with a schema reduces free-form hallucination and makes downstream parsing reliable.")
_add(["ai", "llm"], "Fine-Tuning vs Prompting Tradeoffs",
     "Fine-tuning gives better domain performance but requires data and compute. Few-shot prompting is cheaper and more flexible for most use cases.")
_add(["ai", "llm"], "Hallucination Remains an Open Challenge",
     "LLMs confidently generate plausible but false information. Retrieval-augmented generation and citation grounding are current best mitigations.")
_add(["ai", "prompt-engineering"], "Role Prompting Shapes Response Style",
     "Assigning a role like 'You are an expert data scientist' meaningfully changes the depth and vocabulary of model responses.")
_add(["ai", "llm"], "Quantization Enables Local Model Deployment",
     "4-bit quantization reduces model size by 4x with minimal quality loss, making 7B-13B parameter models runnable on consumer hardware.")
_add(["ai", "programming"], "Code Generation Needs Human Verification",
     "AI-generated code passes syntax checks but may contain subtle logic errors, security vulnerabilities, or edge-case failures that only human review catches.")
_add(["ai", "llm"], "Multimodal Models Unify Vision and Language",
     "Models like GPT-4V process images and text jointly, enabling tasks like diagram interpretation, UI-to-code conversion, and visual QA.")
_add(["ai", "prompt-engineering"], "Prompt Chaining Breaks Complex Tasks",
     "Decomposing a complex prompt into a chain of simpler prompts yields better results than one monolithic instruction.", "article")
_add(["ai", "llm"], "Retrieval Augmented Generation Grounds Output",
     "RAG fetches relevant documents before generation, reducing hallucination and enabling models to cite sources accurately.")
_add(["ai", "llm"], "Scaling Laws Predict Model Performance",
     "Model performance improves predictably with compute, data, and parameters following power laws. This helps plan training budgets.")
_add(["ai", "prompt-engineering"], "Negative Prompting Clarifies Boundaries",
     "Telling a model what NOT to do ('do not include code examples') is often more effective than only describing what you want.")
_add(["ai", "llm"], "KV Cache Optimization Speeds Inference",
     "Caching key-value pairs from previous tokens avoids redundant computation during autoregressive generation, cutting latency significantly.")
_add(["ai", "programming"], "LLM-Powered Test Generation Is Promising",
     "LLMs can generate unit tests from function signatures and docstrings, achieving 60-80% line coverage on typical Python code.")
_add(["ai", "llm"], "Constitutional AI Reduces Harmful Outputs",
     "Training models to self-critique against a set of principles reduces toxic outputs without extensive human labeling.")
_add(["ai", "prompt-engineering"], "Meta-Prompting Teaches Models to Prompt",
     "A meta-prompt instructs the model to generate its own optimal prompt for a task, sometimes outperforming hand-crafted prompts.")
_add(["ai", "llm"], "Long Context Models Change Document Processing",
     "Models with 100K+ token context windows can process entire books, eliminating the need for complex chunking strategies.")
_add(["ai", "llm"], "Speculative Decoding Accelerates Generation",
     "Using a small draft model to propose tokens that a larger model verifies can speed up inference 2-3x without quality loss.")
_add(["ai", "prompt-engineering"], "Persona Consistency Improves Multi-Turn Chats",
     "Maintaining consistent persona instructions across conversation turns prevents the model from drifting in style or expertise level.")
_add(["ai", "llm"], "Instruction Tuning Improves Zero-Shot Ability",
     "Models trained on diverse instruction-following datasets generalize better to unseen tasks than base language models.", "article")
_add(["ai", "programming"], "Cursor-Style AI Editors Change Coding Workflow",
     "IDE-integrated AI that sees your entire codebase context produces more accurate suggestions than standalone chatbot-style coding assistants.")
_add(["ai", "llm"], "Model Distillation Transfers Knowledge Efficiently",
     "A small student model trained on a larger teacher model's outputs can achieve 90% of the teacher's quality at 10% of the compute cost.")
_add(["ai", "prompt-engineering"], "Output Length Control Matters for UX",
     "Explicitly specifying desired output length ('respond in 2-3 sentences') prevents models from over-explaining or being too terse.")
_add(["ai", "llm"], "Mixture of Agents Combines Diverse Strengths",
     "Routing different subtasks to specialized models and aggregating results often outperforms a single general-purpose model.")
_add(["ai", "llm"], "Safety Training Can Reduce Model Capability",
     "Overly aggressive safety fine-tuning can make models refuse legitimate requests. Calibrating the safety-capability tradeoff is crucial.")
_add(["ai", "programming"], "AI Code Review Catches Different Bugs Than Humans",
     "AI reviewers excel at finding style inconsistencies and common patterns but miss architectural issues and business logic errors.")
_add(["ai", "prompt-engineering"], "Delimiter Tokens Prevent Prompt Injection",
     "Wrapping user input in clear delimiters like XML tags helps models distinguish instructions from data, reducing injection attacks.")
_add(["ai", "llm"], "Preference Optimization Replaces Reward Models",
     "Direct preference optimization (DPO) simplifies RLHF by training directly on preference pairs without a separate reward model.")
_add(["ai", "llm"], "Synthetic Data Bootstraps Training Pipelines",
     "Using LLMs to generate training data for smaller models is cost-effective but risks amplifying the teacher model's biases.")
_add(["ai", "programming"], "Natural Language to SQL Is Production-Ready",
     "Modern LLMs can reliably translate natural language queries to SQL for well-documented schemas, enabling non-technical data access.")
_add(["ai", "prompt-engineering"], "ReAct Pattern Combines Reasoning and Acting",
     "The ReAct framework interleaves chain-of-thought reasoning with tool calls, enabling models to plan, execute, and observe iteratively.")
_add(["ai", "llm"], "Sparse Attention Reduces Quadratic Cost",
     "Attention mechanisms that attend to only a subset of tokens (local + global) reduce memory from O(n^2) to O(n log n).")
_add(["ai", "llm"], "Post-Training Quantization Is Surprisingly Effective",
     "GPTQ and AWQ quantization methods preserve model quality even at 4-bit precision, making deployment on edge devices practical.")
_add(["ai", "prompt-engineering"], "Tree of Thoughts Explores Multiple Paths",
     "Generating multiple reasoning branches and evaluating them improves performance on tasks requiring exploration and backtracking.")
_add(["ai", "llm"], "Continual Learning Prevents Catastrophic Forgetting",
     "Training on new data without forgetting old knowledge remains challenging. Elastic weight consolidation and replay buffers help but don't fully solve it.")
_add(["ai", "programming"], "Function Calling Enables Reliable Tool Use",
     "Structured function calling APIs let LLMs invoke external tools with typed arguments, replacing fragile regex-based output parsing.")

# ── Learning / PKM (~40) ────────────────────────────────────────────────

_add(["learning"], "Spaced Repetition Improves Long-Term Retention",
     "Reviewing material at increasing intervals exploits the forgetting curve. SRS achieves 90%+ retention with just 10-15 minutes daily.", "article")
_add(["learning"], "Active Recall Beats Passive Review",
     "Testing yourself on material strengthens memory traces far more effectively than re-reading or highlighting.", "article")
_add(["learning"], "Interleaving Topics Improves Transfer",
     "Mixing different subjects during study sessions improves the ability to discriminate between problem types and apply the right approach.")
_add(["learning"], "Desirable Difficulty Strengthens Learning",
     "Making learning slightly harder — through spacing, interleaving, or retrieval practice — leads to better long-term retention.")
_add(["learning"], "Elaborative Interrogation Deepens Understanding",
     "Asking 'why does this work?' and 'how does this connect to what I know?' forces deeper processing than passive reading.", "flash")
_add(["learning", "pkm"], "The Feynman Technique Tests True Understanding",
     "If you can't explain a concept in simple terms, you don't truly understand it. Teaching forces you to identify gaps in your knowledge.")
_add(["learning"], "Metacognition Separates Expert from Novice Learners",
     "Expert learners monitor their own comprehension, adjust strategies when confused, and accurately predict test performance.")
_add(["learning"], "Sleep Consolidates Procedural and Declarative Memory",
     "Both REM and slow-wave sleep phases play distinct roles in consolidating different types of memories learned during the day.", "article")
_add(["learning", "pkm"], "Integrating SRS into Daily Workflow",
     "Linking spaced repetition cards to active projects and real problems increases motivation and makes reviews feel productive.")
_add(["learning"], "Dual Coding Combines Visual and Verbal Memory",
     "Representing information both visually (diagrams) and verbally (text) creates two independent memory traces, improving recall.")
_add(["learning"], "Generation Effect Enhances Memory",
     "Generating an answer before seeing the correct one — even if wrong — improves subsequent learning compared to passive study.")
_add(["learning"], "Contextual Interference Slows Practice but Aids Transfer",
     "Random practice order feels harder and produces slower initial gains, but leads to better performance in novel situations.")
_add(["learning"], "Distributed Practice Outperforms Massed Practice",
     "Spreading study sessions across days is more effective than cramming the same total time into one session.")
_add(["learning"], "Testing Effect Is One of the Most Robust Findings",
     "Taking practice tests enhances long-term retention more than any other study technique. The effect is large and reliable.", "article")
_add(["learning"], "Concrete Examples Anchor Abstract Concepts",
     "Learners understand abstract principles better when given multiple concrete examples first, then asked to identify the common pattern.")
_add(["pkm"], "Zettelkasten Atomic Notes Principle",
     "Each note should contain exactly one idea, expressed in your own words. Atomicity makes notes maximally composable and reusable.")
_add(["pkm"], "Linking Notes Creates Emergent Structure",
     "Bottom-up linking between atomic notes creates emergent clusters of related ideas, surfacing patterns you didn't plan for.", "flash")
_add(["pkm"], "Progressive Summarization for Note Processing",
     "Highlight key passages on first read, bold the highlights on second read, summarize in your own words on third read. Each layer adds value.")
_add(["pkm"], "Capture Everything Process Later Principle",
     "Separating capture from processing reduces friction. Quick capture preserves fleeting ideas; scheduled processing ensures quality.", "flash")
_add(["pkm"], "Evergreen Notes Evolve Over Time",
     "Unlike static reference notes, evergreen notes are continuously refined as your understanding deepens. They represent your current best thinking.")
_add(["pkm"], "MOCs Bridge Atomic Notes and Projects",
     "Maps of Content (MOCs) are curated index notes that organize atomic notes around a theme without imposing rigid hierarchies.")
_add(["pkm"], "Friction-Free Capture Increases Idea Volume",
     "Reducing the steps between having a thought and recording it dramatically increases the number of ideas that make it into your system.")
_add(["pkm"], "Note Titles Should Be Complete Assertions",
     "Titling a note 'Spaced repetition improves retention' rather than 'Spaced repetition' makes the note's claim immediately scannable.", "article")
_add(["pkm"], "Bidirectional Links Surface Hidden Connections",
     "Backlinks reveal notes that reference the current note, surfacing connections you may not have explicitly created.")
_add(["pkm"], "Weekly Review Prevents PKM System Decay",
     "Without regular review, inboxes overflow and notes go stale. A weekly 30-minute review keeps the system alive and trustworthy.")
_add(["pkm"], "Tags vs Folders: Both Have Tradeoffs",
     "Folders enforce single classification; tags allow multiple. The best systems use folders for broad categories and tags for cross-cutting themes.")
_add(["pkm"], "Graph View Reveals Knowledge Clusters",
     "Visual graph views in tools like Obsidian help identify densely connected clusters and isolated orphan notes that need linking.")
_add(["pkm", "learning"], "Spaced Writing Strengthens Original Thinking",
     "Writing short reflections on your notes at spaced intervals forces you to re-engage with ideas and develop original perspectives.")
_add(["pkm"], "Incremental Reading for Research Papers",
     "Reading papers in small increments and extracting key claims into atomic notes is more effective than trying to digest a whole paper at once.", "article")
_add(["pkm"], "Literature Notes Are Intermediate Processing",
     "Literature notes summarize source material in your own words. They sit between raw highlights and fully processed evergreen notes.")
_add(["pkm"], "Digital Gardens versus Traditional Blogs",
     "Digital gardens publish notes at varying levels of maturity, inviting readers into your thinking process rather than presenting polished essays.", "article")
_add(["learning"], "Retrieval Practice Works Across Domains",
     "The testing effect has been replicated in medicine, law, language learning, and STEM. It is not limited to rote memorization.")
_add(["learning"], "Elaboration Creates Retrieval Cues",
     "Connecting new information to existing knowledge creates multiple retrieval paths, making the information accessible from different angles.")
_add(["learning", "pkm"], "Concept Mapping Externalizes Mental Models",
     "Drawing concept maps forces you to make relationships between ideas explicit, revealing gaps and misconceptions in your understanding.")
_add(["learning"], "Self-Explanation Improves Problem Solving",
     "Explaining each step of a worked example to yourself — even silently — significantly improves ability to solve similar problems.")
_add(["learning"], "Productive Failure Outperforms Direct Instruction",
     "Attempting to solve problems before receiving instruction leads to deeper understanding than being shown the solution first.")
_add(["pkm"], "Personal Knowledge Graphs Enable Serendipity",
     "Dense interconnections between notes increase the probability of stumbling upon unexpected but valuable connections during browsing.")
_add(["learning"], "Motivation Follows Competence Not Vice Versa",
     "People become motivated by activities they feel competent at. Building early wins and visible progress drives sustained engagement.")
_add(["pkm"], "PARA Method Organizes by Actionability",
     "Projects, Areas, Resources, Archives — organizing by actionability rather than topic ensures your system serves your current priorities.")

# ── Productivity / Writing (~40) ────────────────────────────────────────

_add(["productivity"], "Deep Work Requires Deliberate Environment Design",
     "Cal Newport's deep work philosophy: schedule distraction-free blocks, create rituals, and design your environment to minimize context switching.", "article")
_add(["productivity"], "Time Blocking Beats Todo Lists",
     "Assigning specific time slots to tasks forces realistic planning. Todo lists create an illusion of productivity without commitment to execution.")
_add(["productivity"], "Two-Minute Rule Prevents Small Task Buildup",
     "If a task takes less than two minutes, do it immediately. This prevents small tasks from accumulating into overwhelming backlogs.", "flash")
_add(["productivity"], "Energy Management Trumps Time Management",
     "Matching task difficulty to energy levels is more effective than trying to squeeze more hours from the day. Do creative work at peak energy.")
_add(["productivity"], "Batching Similar Tasks Reduces Context Switching",
     "Processing all emails, code reviews, or meetings in dedicated blocks reduces the cognitive cost of switching between different activity types.")
_add(["productivity"], "Weekly Planning Connects Daily Work to Goals",
     "A 30-minute weekly planning session that reviews goals and schedules key tasks ensures daily work aligns with longer-term objectives.")
_add(["productivity"], "Parkinson's Law: Work Expands to Fill Time",
     "Setting artificially tight deadlines forces focus and prevents perfectionism. Most tasks can be done in half the time if constrained.")
_add(["productivity"], "Decision Fatigue Degrades Quality Throughout Day",
     "Making many small decisions depletes willpower. Automate or batch routine decisions to preserve cognitive resources for important choices.")
_add(["productivity"], "Eisenhower Matrix Clarifies Priority",
     "Sorting tasks by urgent vs important reveals that most urgent tasks aren't important, and important tasks rarely feel urgent.")
_add(["productivity"], "Single-Tasking Outperforms Multitasking",
     "Cognitive research consistently shows that focusing on one task at a time produces faster, higher-quality results than attempting to multitask.")
_add(["productivity"], "Default Diary Creates Structure for Flexible Work",
     "Pre-scheduling recurring blocks for deep work, admin, and exercise creates a reliable rhythm without requiring daily planning decisions.")
_add(["productivity"], "Accountability Partners Double Completion Rates",
     "Sharing goals and progress with an accountability partner increases follow-through from ~40% to ~76% according to ASTD research.")
_add(["productivity"], "Process Goals Beat Outcome Goals",
     "Focusing on 'write for 30 minutes daily' rather than 'finish the book' provides clear daily actions and reduces anxiety about results.")
_add(["productivity"], "Maker vs Manager Schedule Conflict",
     "Makers need long uninterrupted blocks; managers need many short meetings. Awareness of this conflict helps teams negotiate protected time.", "article")
_add(["productivity"], "Pomodoro Technique Provides Focus Scaffolding",
     "25-minute focused work sessions with 5-minute breaks provide structure for those who struggle with open-ended deep work blocks.")
_add(["productivity"], "Automation Should Target Recurring Friction",
     "Automate tasks you do repeatedly that cause friction, not tasks that are merely time-consuming. Friction erodes motivation over time.", "flash")
_add(["productivity"], "Environment Design Beats Willpower",
     "Removing distractions from your environment is more reliable than resisting them. Close tabs, silence notifications, use website blockers.")
_add(["productivity"], "Review Cadences Prevent System Drift",
     "Daily, weekly, monthly, and quarterly reviews at different zoom levels keep your productivity system aligned with evolving priorities.")
_add(["writing"], "Separate Drafting from Editing Phases",
     "Writing and editing use different cognitive modes. Switching between them mid-sentence kills flow. Draft first, edit later in a separate session.")
_add(["writing"], "Outline First Then Fill In Details",
     "Starting with a hierarchical outline before writing prose ensures logical structure and prevents the rambling that comes from stream-of-consciousness writing.", "article")
_add(["writing"], "Writing Is Thinking Made Visible",
     "The act of writing doesn't just communicate existing thoughts — it generates new ones. Writing is a thinking tool, not just an output.", "flash")
_add(["writing"], "Plain Language Increases Reader Comprehension",
     "Using simple words, short sentences, and active voice makes writing accessible to broader audiences without sacrificing precision.")
_add(["writing"], "Hemingway's Iceberg Theory of Prose",
     "The best writing implies more than it states. Cutting visible complexity while maintaining underlying depth creates powerful, resonant prose.", "article")
_add(["writing"], "Daily Writing Habit Compounds Over Time",
     "Writing 500 words daily produces 180,000 words per year — enough for two books. Consistency matters more than volume per session.")
_add(["writing"], "Reading Widely Improves Writing Quality",
     "Exposure to diverse writing styles, genres, and disciplines unconsciously expands your vocabulary, rhythm, and structural repertoire.")
_add(["writing"], "Revision Is Where Good Writing Happens",
     "First drafts capture ideas; revision shapes them into clear arguments. Professional writers typically revise 3-5 times before publishing.")
_add(["writing"], "Write for One Specific Reader",
     "Imagining a single real person as your reader helps maintain consistent tone, appropriate complexity, and genuine engagement.")
_add(["writing"], "Show Don't Tell Applies Beyond Fiction",
     "In technical writing, showing a concrete example before explaining the abstract principle helps readers build intuition faster.")
_add(["writing"], "Transitions Are the Skeleton of Good Writing",
     "Clear transitions between paragraphs and sections guide readers through your argument. Without them, even good ideas feel disconnected.")
_add(["writing"], "Kill Your Darlings Improves Clarity",
     "Deleting clever but unnecessary sentences improves overall clarity. If a passage doesn't serve the reader's understanding, remove it.")
_add(["writing"], "Writing in Public Accelerates Feedback Loops",
     "Publishing work-in-progress writing invites feedback that improves both the writing and your thinking about the subject.", "article")
_add(["productivity"], "Saying No Is the Most Productive Habit",
     "Every yes to a low-value commitment is a no to something more important. Protecting your time requires deliberate, uncomfortable refusals.")
_add(["productivity"], "Morning Routines Reduce Decision Overhead",
     "A consistent morning routine eliminates dozens of small decisions, preserving willpower for the creative and strategic work that follows.")
_add(["writing"], "Active Voice Creates Stronger Sentences",
     "Replacing 'the code was reviewed by the team' with 'the team reviewed the code' creates shorter, clearer, more direct sentences.")
_add(["writing"], "Constraints Boost Creative Output",
     "Word limits, time limits, and format constraints force creative problem-solving and prevent the paralysis of infinite possibilities.")
_add(["productivity"], "Input Filtering Protects Attention Quality",
     "Curating information sources aggressively — unsubscribing, unfollowing, blocking — protects the quality of ideas entering your mind.")
_add(["writing"], "Technical Writing Needs Concrete Examples",
     "Abstract explanations without concrete examples force readers to build mental models from scratch. Examples anchor understanding immediately.")
_add(["productivity"], "Keystone Habits Create Positive Cascades",
     "Some habits — exercise, meditation, journaling — trigger positive changes across other life domains. Identify and prioritize these keystone habits.")

# ── Programming (~40) ───────────────────────────────────────────────────

_add(["programming"], "Test-Driven Development Reduces Bug Density",
     "Writing tests before code forces clear thinking about interfaces and edge cases. TDD codebases have 40-80% fewer production bugs.", "article")
_add(["programming"], "Composition Over Inheritance Principle",
     "Favoring composition creates more flexible, testable code. Inheritance hierarchies become brittle and hard to refactor as requirements change.")
_add(["programming"], "Immutability Eliminates Shared State Bugs",
     "Immutable data structures prevent entire categories of concurrency bugs. The performance cost is negligible for most applications.")
_add(["programming"], "API Design Should Follow Conventions",
     "RESTful APIs should use standard HTTP methods, status codes, and naming conventions. Consistency reduces learning curve and integration errors.", "article")
_add(["programming"], "Database Indexes Are Not Free",
     "Each index speeds reads but slows writes and consumes storage. Profile query patterns before adding indexes; remove unused ones.", "flash")
_add(["programming"], "Dependency Injection Makes Code Testable",
     "Injecting dependencies rather than hard-coding them enables easy mocking in tests and flexible swapping of implementations.")
_add(["programming"], "Graph Databases Model Knowledge Naturally",
     "For domains with complex relationships — social networks, knowledge graphs, recommendation systems — graph databases outperform relational models.", "article")
_add(["programming"], "Feature Flags Decouple Deploy from Release",
     "Deploying code behind feature flags allows gradual rollout, instant rollback, and A/B testing without separate deployment pipelines.")
_add(["programming"], "Observability Beats Traditional Monitoring",
     "Structured logging, distributed tracing, and metrics provide the ability to ask arbitrary questions about system behavior, not just pre-defined alerts.")
_add(["programming"], "Event Sourcing Provides Complete Audit Trail",
     "Storing every state change as an immutable event enables time-travel debugging, audit compliance, and rebuilding projections from scratch.")
_add(["programming"], "Trunk-Based Development Reduces Merge Pain",
     "Short-lived feature branches merged daily prevent the integration hell of long-lived branches. CI/CD pipelines catch issues immediately.")
_add(["programming"], "Type Systems Catch Errors at Compile Time",
     "Strong static typing catches categories of bugs — null references, type mismatches, missing fields — before code ever runs.", "article")
_add(["programming"], "Idempotency Is Critical for Distributed Systems",
     "Making operations safe to retry without side effects simplifies error handling and enables reliable message processing in distributed architectures.")
_add(["programming"], "CQRS Separates Read and Write Models",
     "Command Query Responsibility Segregation allows optimizing read and write paths independently, crucial for high-throughput systems.")
_add(["programming"], "Circuit Breakers Prevent Cascade Failures",
     "When a downstream service fails, circuit breakers stop sending requests, allowing the system to degrade gracefully rather than cascading.")
_add(["programming"], "Semantic Versioning Communicates Intent",
     "SemVer (MAJOR.MINOR.PATCH) tells consumers whether an update is safe. Breaking changes increment MAJOR; features increment MINOR.", "flash")
_add(["programming"], "Twelve-Factor App Methodology for Cloud Native",
     "The twelve-factor methodology provides a checklist for building cloud-native applications: config in env vars, stateless processes, disposable instances.")
_add(["programming"], "Premature Optimization Is Still the Root of Evil",
     "Profile before optimizing. Most performance assumptions are wrong. The hot path is usually not where you expect it to be.", "flash")
_add(["programming"], "Code Review Is a Teaching Opportunity",
     "The best code reviews educate both author and reviewer. Focus on 'why' rather than 'what' — understanding intent prevents future issues.")
_add(["programming"], "Monorepos Simplify Dependency Management",
     "Keeping all related code in one repository ensures consistent versioning, atomic cross-package changes, and simplified CI configuration.")
_add(["programming"], "Error Handling Should Be Explicit Not Silent",
     "Catching and silently swallowing exceptions hides bugs. Errors should be handled explicitly — log, retry, or propagate with context.")
_add(["programming"], "Infrastructure as Code Enables Reproducibility",
     "Defining infrastructure in version-controlled code ensures environments are reproducible, auditable, and recoverable from disasters.")
_add(["programming"], "Rate Limiting Protects System Resources",
     "Token bucket or sliding window rate limiters prevent abuse and ensure fair resource allocation among API consumers.")
_add(["programming"], "Database Migrations Should Be Reversible",
     "Every migration should have a corresponding rollback. Irreversible migrations (dropping columns) need careful data backup strategies.")
_add(["programming"], "Microservices Add Operational Complexity",
     "Microservices solve organizational scaling but add distributed systems complexity. Start with a monolith and extract services when boundaries are clear.")
_add(["programming"], "Functional Core Imperative Shell Pattern",
     "Keep business logic in pure functions (functional core) and I/O in a thin outer layer (imperative shell). This maximizes testability.")
_add(["programming"], "Property-Based Testing Finds Edge Cases",
     "Generating random inputs based on type properties finds edge cases that example-based tests miss. Hypothesis and QuickCheck are excellent tools.")
_add(["programming"], "Dead Code Should Be Deleted Not Commented",
     "Version control preserves history. Commented-out code adds noise, confuses readers, and never gets uncommented. Delete it confidently.")
_add(["programming"], "Structured Logging Enables Machine Analysis",
     "Logging structured JSON instead of free-text strings enables filtering, aggregation, and alerting across millions of log entries.")
_add(["programming"], "Graceful Degradation Beats Hard Failure",
     "When a non-critical dependency fails, serve cached or default data rather than returning an error. Users prefer partial results to no results.")
_add(["programming"], "Contract Testing Validates Service Boundaries",
     "Consumer-driven contracts verify that service changes don't break callers, without the fragility and cost of full integration tests.")
_add(["programming"], "Blue-Green Deployments Enable Zero Downtime",
     "Running two identical production environments and switching traffic between them eliminates deployment downtime and enables instant rollback.")
_add(["programming"], "Chaos Engineering Builds Confidence in Resilience",
     "Intentionally injecting failures in production reveals weaknesses before they cause outages. Start small with controlled experiments.")
_add(["programming"], "Domain-Driven Design Aligns Code with Business",
     "Using ubiquitous language from the business domain in code reduces translation errors between stakeholders and developers.")
_add(["programming"], "Pagination Should Use Cursor Not Offset",
     "Cursor-based pagination is stable under concurrent inserts and performs consistently regardless of page depth, unlike offset-based pagination.")
_add(["programming"], "Cache Invalidation Is Genuinely Hard",
     "Most caching bugs come from stale data. Use TTL with cache-aside pattern, and always have a manual invalidation mechanism for emergencies.")
_add(["programming"], "Git Hooks Automate Quality Gates",
     "Pre-commit hooks running linters, formatters, and type checkers catch issues before they enter the repository, reducing review friction.")
_add(["programming"], "README-Driven Development Clarifies Intent",
     "Writing the README before the code forces you to think about user experience, API design, and documentation from the start.")
_add(["programming"], "Load Testing Should Simulate Real Traffic Patterns",
     "Uniform load tests miss spiky traffic patterns. Use production traffic profiles to model realistic scenarios with tools like k6 or Locust.")

# ── Health / Finance / Philosophy / Psychology (~40) ────────────────────

_add(["health"], "Sleep Quality Affects Cognitive Performance",
     "7-8 hours of quality sleep is the single most impactful intervention for cognitive performance, emotional regulation, and physical health.", "article")
_add(["health"], "Exercise Boosts Brain-Derived Neurotrophic Factor",
     "Aerobic exercise increases BDNF, a protein that supports learning, memory, and neuroplasticity. Even 20 minutes of walking helps.", "article")
_add(["health"], "Caffeine Has a Six-Hour Half-Life",
     "A cup of coffee at 3 PM means half the caffeine is still active at 9 PM, significantly impacting sleep quality even if you fall asleep.", "flash")
_add(["health"], "Hydration Directly Impacts Focus",
     "Even mild dehydration (1-2% body weight loss) impairs concentration, working memory, and mood. Keep water visible and accessible.")
_add(["health"], "Posture Affects Energy and Mood",
     "Ergonomic posture reduces fatigue and chronic pain. Standing desks, monitor height, and regular stretching prevent the programmer's slouch.")
_add(["health"], "Meditation Reduces Default Mode Network Activity",
     "Regular meditation practice reduces mind-wandering and rumination by quieting the brain's default mode network.", "article")
_add(["health"], "Blue Light Before Bed Suppresses Melatonin",
     "Screen light in the blue spectrum delays melatonin production by up to 90 minutes. Use night mode or blue-light glasses after sunset.")
_add(["health"], "Micro-Breaks Prevent Repetitive Strain Injuries",
     "Taking 30-second breaks every 20 minutes to look away from screens and stretch hands prevents cumulative strain injuries.")
_add(["health"], "Nutrition Impacts Sustained Mental Energy",
     "Complex carbohydrates, healthy fats, and protein provide sustained energy. Simple sugars cause spikes and crashes that impair focus.")
_add(["health"], "Social Connection Protects Against Burnout",
     "Strong social connections at work reduce burnout risk by 50%. Regular non-work conversations with colleagues build psychological safety.")
_add(["finance"], "Side Projects Need Clear Revenue Models",
     "Starting a side project without a clear path to revenue leads to burnout. Define the business model before writing the first line of code.", "article")
_add(["finance"], "Compound Interest Applies to Skills Too",
     "Investing 1 hour daily in a skill compounds over years. A 1% daily improvement leads to 37x growth in a year. Start small, stay consistent.")
_add(["finance"], "Validate Ideas Before Building Full Products",
     "A landing page, waitlist, or manual MVP tests demand before you invest months of development time. Most ideas don't survive contact with users.", "article")
_add(["finance"], "Pricing Should Reflect Value Not Cost",
     "Cost-plus pricing leaves money on the table. Price based on the value your product creates for customers, not what it costs you to make.")
_add(["finance"], "Recurring Revenue Beats One-Time Sales",
     "SaaS and subscription models provide predictable revenue and higher lifetime value. One-time sales require constant customer acquisition.")
_add(["finance"], "Emergency Fund Enables Career Risk-Taking",
     "6 months of expenses saved enables career moves — quitting toxic jobs, starting businesses, or taking sabbaticals — without financial panic.")
_add(["finance"], "Dollar-Cost Averaging Removes Timing Risk",
     "Investing a fixed amount on a regular schedule regardless of market conditions removes the impossible task of timing market highs and lows.")
_add(["finance"], "Technical Debt Accrues Financial Interest",
     "Like financial debt, technical debt has carrying costs. Each shortcut taken now increases the cost of future changes. Track and budget for it.")
_add(["finance"], "Open Source Can Be a Business Strategy",
     "Open-sourcing builds trust, community, and distribution. Monetize through hosted services, support contracts, or premium features.")
_add(["finance"], "Time Tracking Reveals True Cost of Activities",
     "Tracking where your time goes for one week often reveals shocking inefficiencies. You can't optimize what you don't measure.")
_add(["philosophy"], "Stoic Dichotomy of Control Reduces Anxiety",
     "Focusing only on what you can control (your actions, reactions) and accepting what you cannot (others' behavior, outcomes) reduces pointless anxiety.", "article")
_add(["philosophy"], "Ikigai Sits at the Intersection of Four Elements",
     "Purpose emerges where what you love, what you're good at, what the world needs, and what you can be paid for overlap.")
_add(["philosophy"], "Second-Order Thinking Prevents Unintended Consequences",
     "Asking 'and then what?' after each decision reveals downstream effects. First-order thinkers optimize locally; second-order thinkers optimize globally.")
_add(["philosophy"], "Via Negativa: Improvement Through Subtraction",
     "Often the best improvement comes from removing harmful practices rather than adding new ones. Stop bad habits before starting good ones.", "article")
_add(["philosophy"], "Antifragility Benefits from Disorder",
     "Systems that gain from volatility and stress are antifragile. Building redundancy and optionality into systems makes them stronger through adversity.")
_add(["philosophy"], "Hanlons Razor Prevents Unnecessary Conflict",
     "Never attribute to malice what is adequately explained by ignorance or oversight. This heuristic prevents escalating misunderstandings.")
_add(["philosophy"], "Inversion Thinking Solves Problems Backwards",
     "Instead of asking 'how do I succeed?', ask 'how would I guarantee failure?' and avoid those paths. Inversion reveals blind spots.")
_add(["philosophy"], "Skin in the Game Aligns Incentives",
     "People make better decisions when they bear the consequences. Systems where decision-makers have skin in the game are more robust.", "article")
_add(["psychology"], "Dunning-Kruger Effect Explains Confidence Gaps",
     "Beginners overestimate their competence while experts underestimate theirs. This asymmetry creates dangerous false confidence in complex domains.")
_add(["psychology"], "Flow State Requires Challenge-Skill Balance",
     "Mihaly Csikszentmihalyi's flow occurs when task difficulty slightly exceeds current skill level. Too easy causes boredom; too hard causes anxiety.")
_add(["psychology"], "Anchoring Bias Distorts Numerical Estimates",
     "The first number encountered in a negotiation or estimate disproportionately influences the final result. Set anchors deliberately.")
_add(["psychology"], "Confirmation Bias Is the Most Pervasive Cognitive Trap",
     "We unconsciously seek, interpret, and remember information that confirms existing beliefs. Active disconfirmation is the antidote.")
_add(["psychology"], "Loss Aversion Makes Us Irrationally Conservative",
     "Losses feel roughly twice as painful as equivalent gains feel good. This bias makes us avoid beneficial risks and cling to sunk costs.")
_add(["psychology"], "Cognitive Load Theory Explains Learning Bottlenecks",
     "Working memory can hold only 4-7 items simultaneously. Effective instruction manages intrinsic, extraneous, and germane cognitive load.")
_add(["psychology"], "Growth Mindset Enables Resilience",
     "Believing abilities are developed through effort rather than fixed at birth enables persistence through failure and continuous improvement.", "article")
_add(["psychology"], "Habit Formation Follows the Cue-Routine-Reward Loop",
     "Understanding the cue-routine-reward cycle enables deliberate habit change. Modify the routine while keeping the cue and reward stable.")
_add(["psychology"], "Zeigarnik Effect: Unfinished Tasks Occupy Working Memory",
     "The brain keeps unfinished tasks in working memory, creating mental overhead. Writing tasks down or completing them frees cognitive resources.")
_add(["psychology"], "Paradox of Choice Leads to Decision Paralysis",
     "More options increase anxiety and decrease satisfaction. Limiting choices to 3-5 good options improves both decision speed and contentment.")
_add(["health"], "Walking Meetings Boost Creative Thinking",
     "Stanford research shows walking increases creative output by 60%. Moving meetings outdoors combines exercise, nature exposure, and ideation.")
_add(["health"], "Ultradian Rhythms Govern Focus Cycles",
     "The body cycles through 90-minute high-energy periods followed by 20-minute recovery dips. Aligning work to these rhythms maximizes sustained focus.")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def generate_slug(title: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", title.lower())[:5]
    return "-".join(words) if words else "capture"


def random_timestamp(start: datetime, end: datetime) -> datetime:
    """Generate a random timestamp between start and end."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


# ---------------------------------------------------------------------------
# Step 1: Clear existing content
# ---------------------------------------------------------------------------

def clear_vault():
    """Remove existing content files, keep structure."""
    for subdir in ["captures", "notes", "topics"]:
        d = VAULT / subdir
        if d.exists():
            for f in d.iterdir():
                if f.name != ".gitkeep" and not f.name.startswith("."):
                    f.unlink()

    # Reset .brain
    brain = VAULT / ".brain"
    (brain / "graph.json").write_text('{"nodes":[],"edges":[],"generation":0,"updated_at":null}\n')
    (brain / "clusters.json").write_text('{"clusters":[],"graph_generation":0,"updated_at":null}\n')
    (brain / "review-log.json").write_text('{"reviews":[],"last_reviewed_at":null}\n')


# ---------------------------------------------------------------------------
# Step 2: Generate 1000 captures
# ---------------------------------------------------------------------------

def generate_captures() -> list[dict]:
    """Generate 1000 capture files. Returns list of capture metadata."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 3, 20, tzinfo=timezone.utc)

    # We have ~200 unique insights. Expand to 1000 by creating variations.
    # Each original insight gets ~5 variations with slightly different framing.
    expanded: list[dict] = []

    variation_prefixes = [
        ("", ""),  # original
        ("Practical Application: ", "In practice, "),
        ("Key Insight: ", "The key realization is that "),
        ("Research Finding: ", "Studies show that "),
        ("Lesson Learned: ", "Experience teaches that "),
    ]

    for i, capture in enumerate(CAPTURES):
        for vi, (title_prefix, insight_prefix) in enumerate(variation_prefixes):
            if vi == 0:
                t = capture["title"]
                ins = capture["insight"]
            else:
                t = f"{title_prefix}{capture['title']}"[:50]
                ins = f"{insight_prefix}{capture['insight'][0].lower()}{capture['insight'][1:]}"

            expanded.append({
                "tags": capture["tags"],
                "title": t,
                "insight": ins,
                "source": capture["source"],
                "group_id": i,  # for later grouping
            })

    # Shuffle and take 1000
    random.seed(42)
    random.shuffle(expanded)
    captures = expanded[:1000]

    # Assign timestamps
    timestamps = sorted([random_timestamp(start_date, end_date) for _ in range(1000)])

    results = []
    for cap, ts in zip(captures, timestamps):
        slug = generate_slug(cap["title"])
        ts_str = ts.strftime("%Y-%m-%d-%H%M%S")
        filename = f"captures/{ts_str}-{slug}.md"

        metadata = {
            "title": cap["title"],
            "status": "capture",
            "created": ts.isoformat(),
            "updated": ts.isoformat(),
            "source": cap["source"],
            "tags": cap["tags"],
            "aliases": [],
        }

        post = frontmatter.Post(cap["insight"], **metadata)
        content = frontmatter.dumps(post)

        filepath = VAULT / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

        results.append({
            "path": filename,
            "title": cap["title"],
            "tags": cap["tags"],
            "insight": cap["insight"],
            "group_id": cap["group_id"],
            "created": ts.isoformat(),
        })

    return results


# ---------------------------------------------------------------------------
# Step 3: Promote captures → notes
# ---------------------------------------------------------------------------

# Pre-defined note synthesis plans: (title, domain, summary, key_points, aliases, confidence)
NOTE_PLANS = [
    # AI / LLM
    ("Transformer Architecture Fundamentals", "ai",
     "The transformer architecture uses self-attention to enable parallel training at scale, forming the foundation of modern LLMs.",
     ["Self-attention replaces recurrence, enabling massive parallelism during training",
      "Scaling laws predict performance improvements with compute, data, and parameters",
      "Sparse attention variants reduce the quadratic memory cost of standard attention"],
     ["Transformers"], 0.9),
    ("LLM Inference Optimization Techniques", "ai",
     "Multiple techniques — quantization, KV caching, speculative decoding — make large model inference practical on limited hardware.",
     ["4-bit quantization reduces model size 4x with minimal quality loss",
      "KV cache avoids redundant computation during autoregressive generation",
      "Speculative decoding uses a small draft model verified by the larger model for 2-3x speedup"],
     ["LLM Optimization"], 0.85),
    ("Effective LLM Prompt Patterns", "ai",
     "Three core prompt engineering patterns — chain-of-thought, system prompts, and few-shot examples — significantly improve LLM output quality.",
     ["Chain-of-thought prompting improves accuracy 20-40% on complex reasoning tasks",
      "System prompts define persona and constraints for consistent behavior",
      "Few-shot examples help models match desired format and style"],
     ["Prompt Patterns", "Prompt Engineering"], 0.85),
    ("Retrieval Augmented Generation Architecture", "ai",
     "RAG combines retrieval and generation to ground LLM outputs in factual sources, reducing hallucination.",
     ["Fetching relevant documents before generation reduces hallucination",
      "Embedding models map text to vectors where semantic similarity correlates with distance",
      "Long context models may reduce but not eliminate the need for RAG"],
     ["RAG"], 0.8),
    ("AI-Assisted Software Development", "ai",
     "AI coding tools shift developer focus from writing code to reviewing, specifying, and verifying AI-generated code.",
     ["AI pair programming changes the developer role to reviewer and guide",
      "IDE-integrated AI with codebase context outperforms standalone chatbots",
      "AI-generated code needs human review for subtle logic errors and security vulnerabilities"],
     ["AI Coding", "AI Dev"], 0.85),
    ("LLM Safety and Alignment", "ai",
     "Aligning LLMs with human preferences requires balancing safety training against capability preservation.",
     ["RLHF trains models to produce outputs humans prefer",
      "Constitutional AI enables self-critique against principles without extensive human labeling",
      "Overly aggressive safety training can make models refuse legitimate requests"],
     ["AI Safety", "AI Alignment"], 0.75),
    ("Advanced Prompt Engineering Techniques", "ai",
     "Beyond basic prompting, techniques like ReAct, tree-of-thoughts, and meta-prompting push LLM capabilities further.",
     ["ReAct interleaves reasoning with tool calls for iterative plan-execute-observe loops",
      "Tree of thoughts generates multiple reasoning branches and evaluates them",
      "Meta-prompting instructs models to generate their own optimal prompts"],
     ["Advanced Prompting"], 0.8),
    ("Model Training and Fine-Tuning Strategies", "ai",
     "The spectrum from prompting to fine-tuning to distillation offers tradeoffs between cost, flexibility, and domain performance.",
     ["Fine-tuning gives better domain performance but requires data and compute",
      "Model distillation transfers 90% of teacher quality at 10% compute cost",
      "Synthetic data from LLMs can bootstrap training but risks amplifying biases"],
     ["Model Training"], 0.8),
    ("Structured LLM Output Patterns", "ai",
     "Function calling and structured output formats make LLM outputs reliable for programmatic consumption.",
     ["Structured output formats like JSON reduce free-form hallucination",
      "Function calling APIs enable typed tool invocation, replacing fragile regex parsing",
      "Output length control prevents models from over-explaining or being too terse"],
     ["Structured Output"], 0.85),

    # Learning / PKM
    ("Spaced Repetition for Knowledge Workers", "learning",
     "Spaced repetition leverages the forgetting curve and active recall to achieve 90%+ long-term retention with minimal daily time investment.",
     ["SRS schedules reviews at optimal intervals to counteract the forgetting curve",
      "Active recall strengthens memory traces far more than re-reading or highlighting",
      "10-15 minutes of daily review linked to active projects sustains motivation"],
     ["SRS", "Spaced Repetition"], 0.9),
    ("Evidence-Based Study Techniques", "learning",
     "Research identifies retrieval practice, spaced repetition, interleaving, and elaboration as the most effective learning strategies.",
     ["The testing effect is one of the most robust findings in learning science",
      "Interleaving topics improves transfer by forcing discrimination between problem types",
      "Desirable difficulty — making learning slightly harder — leads to better long-term retention"],
     ["Study Techniques", "Learning Science"], 0.9),
    ("Metacognition and Expert Learning", "learning",
     "Expert learners distinguish themselves through metacognitive skills: monitoring comprehension, adjusting strategies, and predicting performance.",
     ["Metacognition separates expert from novice learners",
      "Self-explanation of worked examples significantly improves problem solving",
      "Productive failure — attempting before receiving instruction — deepens understanding"],
     ["Metacognition"], 0.85),
    ("Memory Encoding and Consolidation", "learning",
     "Memory formation depends on encoding depth, sleep consolidation, and creating multiple retrieval paths through elaboration.",
     ["Dual coding combines visual and verbal memory traces for improved recall",
      "Sleep consolidates both procedural and declarative memories",
      "Elaboration connects new information to existing knowledge, creating multiple retrieval paths"],
     ["Memory Science"], 0.85),
    ("Zettelkasten Core Principles", "pkm",
     "The Zettelkasten method centers on atomic notes and emergent structure through linking rather than hierarchical folders.",
     ["Each note captures one idea in your own words for maximum composability",
      "Bottom-up linking creates emergent structure that surfaces unexpected connections",
      "Note titles should be complete assertions making the claim immediately scannable"],
     ["Zettelkasten"], 0.9),
    ("Personal Knowledge Management Systems", "pkm",
     "Effective PKM separates capture from processing, uses progressive summarization, and maintains the system through regular reviews.",
     ["Capture everything, process later — separation reduces friction",
      "Progressive summarization adds value through multiple processing layers",
      "Weekly reviews prevent system decay and keep the system trustworthy"],
     ["PKM Systems"], 0.85),
    ("Note-Taking Architecture and Organization", "pkm",
     "Organizing notes by actionability (PARA) and using MOCs as curated indexes provides both structure and flexibility.",
     ["PARA organizes by actionability: Projects, Areas, Resources, Archives",
      "Maps of Content bridge atomic notes and higher-level themes without rigid hierarchies",
      "Tags allow multiple classification while folders enforce single hierarchy"],
     ["Note Architecture", "Note Organization"], 0.85),
    ("Knowledge Graphs and Digital Gardens", "pkm",
     "Dense interconnections in personal knowledge graphs enable serendipitous discovery, while digital gardens publish thinking-in-progress.",
     ["Graph views reveal knowledge clusters and orphan notes needing connections",
      "Bidirectional links surface hidden connections through backlinks",
      "Digital gardens publish notes at varying maturity levels, inviting collaboration"],
     ["Knowledge Graphs", "Digital Gardens"], 0.8),
    ("Incremental Reading and Literature Processing", "pkm",
     "Processing research papers incrementally through literature notes builds understanding more effectively than consuming whole papers at once.",
     ["Reading papers in small increments with atomic note extraction is more effective",
      "Literature notes are intermediate processing between raw highlights and evergreen notes",
      "Concept mapping externalizes mental models, revealing gaps in understanding"],
     ["Incremental Reading"], 0.8),

    # Productivity / Writing
    ("Deep Work and Focus Management", "productivity",
     "Sustained cognitive performance requires deliberate environment design, energy management, and protection from context switching.",
     ["Deep work requires scheduled distraction-free blocks and environmental design",
      "Energy management — matching task difficulty to energy levels — trumps time management",
      "Single-tasking consistently outperforms multitasking in both speed and quality"],
     ["Deep Work", "Focus"], 0.9),
    ("Time and Task Management Systems", "productivity",
     "Effective task management combines time blocking, priority frameworks, and regular review cadences to connect daily work to goals.",
     ["Time blocking forces realistic planning by committing to specific time slots",
      "The Eisenhower Matrix reveals that most urgent tasks aren't important",
      "Weekly planning sessions connect daily work to longer-term objectives"],
     ["Task Management", "Time Management"], 0.85),
    ("Habit Formation and Behavioral Design", "productivity",
     "Sustainable behavior change leverages environment design, keystone habits, and understanding the cue-routine-reward loop.",
     ["Environment design beats willpower — remove distractions rather than resisting them",
      "Keystone habits like exercise trigger positive cascades across other life domains",
      "Process goals ('write 30 min daily') outperform outcome goals ('finish the book')"],
     ["Habits", "Behavior Design"], 0.85),
    ("Automation and Efficiency Principles", "productivity",
     "Strategic automation targets recurring friction points, while batching reduces context switching costs.",
     ["Automate tasks that cause recurring friction, not merely time-consuming ones",
      "Batching similar tasks in dedicated blocks reduces cognitive switching cost",
      "Parkinson's Law — setting tight deadlines forces focus and prevents perfectionism"],
     ["Automation", "Efficiency"], 0.8),
    ("Writing as a Thinking Tool", "writing",
     "Writing generates new thoughts rather than merely communicating existing ones. Separating drafting from editing enables both creativity and clarity.",
     ["Writing is thinking made visible — it generates ideas, not just communicates them",
      "Separate drafting and editing phases to avoid killing creative flow",
      "Daily writing habit of 500 words compounds to 180,000 words per year"],
     ["Writing Process"], 0.9),
    ("Technical and Nonfiction Writing Craft", "writing",
     "Effective technical writing uses concrete examples, active voice, and clear transitions to guide readers through complex ideas.",
     ["Concrete examples anchor abstract concepts — show before you tell",
      "Active voice creates stronger, shorter, clearer sentences",
      "Transitions are the skeleton of good writing, guiding readers through arguments"],
     ["Technical Writing", "Nonfiction Writing"], 0.85),
    ("Editing and Revision Strategies", "writing",
     "Good writing happens in revision. Cutting unnecessary material, targeting a specific reader, and publishing early all improve quality.",
     ["Professional writers revise 3-5 times before publishing",
      "Kill your darlings — delete clever but unnecessary passages for clarity",
      "Writing for one specific reader maintains consistent tone and complexity"],
     ["Editing", "Revision"], 0.85),
    ("Public Writing and Feedback Loops", "writing",
     "Publishing work-in-progress writing and maintaining constraint-driven practice accelerates both writing skill and idea development.",
     ["Writing in public invites feedback that improves both writing and thinking",
      "Constraints (word limits, formats) boost creative output by preventing paralysis",
      "Outlining before writing ensures logical structure and prevents rambling"],
     ["Public Writing"], 0.8),

    # Programming
    ("Software Testing Strategies", "programming",
     "A comprehensive testing strategy combines TDD, property-based testing, and contract testing to catch different categories of bugs.",
     ["TDD reduces production bug density by 40-80%",
      "Property-based testing finds edge cases that example-based tests miss",
      "Consumer-driven contracts verify service boundaries without full integration tests"],
     ["Testing", "TDD"], 0.9),
    ("API and System Design Patterns", "programming",
     "Well-designed APIs follow conventions, use cursor-based pagination, and separate read/write models for high-throughput systems.",
     ["RESTful APIs should use standard HTTP methods, status codes, and naming conventions",
      "Cursor-based pagination is stable under concurrent inserts unlike offset-based",
      "CQRS separates read and write models for independent optimization"],
     ["API Design", "System Design"], 0.85),
    ("Distributed Systems Resilience", "programming",
     "Building resilient distributed systems requires idempotency, circuit breakers, and graceful degradation strategies.",
     ["Idempotent operations simplify error handling in distributed architectures",
      "Circuit breakers prevent cascade failures by stopping requests to failed services",
      "Graceful degradation serves cached or default data rather than hard errors"],
     ["Distributed Systems", "Resilience"], 0.85),
    ("Code Quality and Maintainability", "programming",
     "Maintainable code favors composition over inheritance, explicit error handling, and deletion of dead code.",
     ["Composition creates more flexible, testable code than inheritance hierarchies",
      "Errors should be handled explicitly — log, retry, or propagate with context",
      "Dead code should be deleted, not commented — version control preserves history"],
     ["Code Quality", "Clean Code"], 0.85),
    ("DevOps and Deployment Practices", "programming",
     "Modern deployment practices — trunk-based development, feature flags, blue-green deploys — enable fast, safe releases.",
     ["Trunk-based development with daily merges prevents integration hell",
      "Feature flags decouple deployment from release, enabling gradual rollout",
      "Blue-green deployments enable zero-downtime releases with instant rollback"],
     ["DevOps", "Deployment", "CI/CD"], 0.85),
    ("Database and Data Architecture", "programming",
     "Data architecture decisions — indexes, migrations, event sourcing — have long-term implications for system performance and auditability.",
     ["Database indexes speed reads but slow writes — profile before adding",
      "Every migration should have a corresponding rollback strategy",
      "Event sourcing stores immutable events for complete audit trail and time-travel debugging"],
     ["Database", "Data Architecture"], 0.8),
    ("Observability and Operational Excellence", "programming",
     "Structured logging, infrastructure as code, and chaos engineering build confidence in system reliability.",
     ["Structured JSON logging enables machine analysis across millions of entries",
      "Infrastructure as code ensures reproducible, auditable environments",
      "Chaos engineering reveals weaknesses before they cause outages"],
     ["Observability", "Operations"], 0.8),
    ("Software Architecture Principles", "programming",
     "Sound architecture uses functional core/imperative shell, domain-driven design, and starts with monoliths before extracting services.",
     ["Functional core / imperative shell maximizes testability",
      "Domain-driven design aligns code with business using ubiquitous language",
      "Start with a monolith and extract microservices when boundaries are clear"],
     ["Architecture", "Software Design"], 0.85),

    # Health / Finance / Philosophy / Psychology
    ("Sleep and Cognitive Performance", "health",
     "Sleep quality is the single most impactful intervention for cognitive performance, with specific mechanisms for memory consolidation.",
     ["7-8 hours of quality sleep is the highest-ROI investment in cognitive performance",
      "Blue light before bed delays melatonin production by up to 90 minutes",
      "Both REM and slow-wave sleep phases consolidate different types of memories"],
     ["Sleep Science"], 0.9),
    ("Physical Health for Knowledge Workers", "health",
     "Exercise, ergonomics, hydration, and micro-breaks prevent the chronic health issues common among sedentary knowledge workers.",
     ["Aerobic exercise increases BDNF, supporting learning and neuroplasticity",
      "Ergonomic posture and regular stretching prevent repetitive strain injuries",
      "Even mild dehydration impairs concentration and working memory"],
     ["Health Optimization", "Knowledge Worker Health"], 0.85),
    ("Energy and Focus Optimization", "health",
     "Aligning work to ultradian rhythms, managing caffeine timing, and using walking meetings optimize sustained mental energy.",
     ["Ultradian rhythms cycle through 90-minute high-energy periods followed by 20-minute dips",
      "Caffeine's 6-hour half-life means afternoon coffee significantly impacts sleep quality",
      "Walking increases creative output by 60% according to Stanford research"],
     ["Energy Management", "Focus Optimization"], 0.85),
    ("Mental Health and Burnout Prevention", "health",
     "Preventing burnout requires social connection, meditation practice, and nutrition strategies for sustained mental energy.",
     ["Strong social connections at work reduce burnout risk by 50%",
      "Meditation reduces default mode network activity, decreasing rumination",
      "Complex carbohydrates and healthy fats provide sustained energy unlike sugar spikes"],
     ["Mental Health", "Burnout Prevention"], 0.8),
    ("Financial Independence for Creators", "finance",
     "Building financial independence requires clear revenue models, validated ideas, recurring revenue streams, and prudent saving.",
     ["Define the business model before writing the first line of code",
      "Recurring revenue (SaaS/subscriptions) provides predictable income and higher LTV",
      "An emergency fund of 6 months expenses enables career risk-taking"],
     ["Creator Finance", "Indie Finance"], 0.8),
    ("Investment and Wealth Building Principles", "finance",
     "Sustainable wealth building uses dollar-cost averaging, value-based pricing, and treats skill development as compound interest.",
     ["Dollar-cost averaging removes the impossible task of timing markets",
      "Pricing should reflect value created for customers, not cost of production",
      "1 hour daily skill investment compounds — 1% daily improvement yields 37x annual growth"],
     ["Investing", "Wealth Building"], 0.8),
    ("Mental Models for Clear Thinking", "philosophy",
     "A toolkit of mental models — inversion, second-order thinking, via negativa — enables better decision-making across domains.",
     ["Inversion reveals blind spots by asking 'how would I guarantee failure?'",
      "Second-order thinking asks 'and then what?' to reveal downstream effects",
      "Via negativa improves by subtraction — stop bad habits before starting good ones"],
     ["Mental Models", "Clear Thinking"], 0.9),
    ("Stoic Philosophy for Modern Life", "philosophy",
     "Stoic principles — dichotomy of control, antifragility, skin in the game — provide practical frameworks for resilience and decision-making.",
     ["Focus only on what you can control; accept what you cannot",
      "Antifragile systems gain from volatility through redundancy and optionality",
      "Skin in the game aligns incentives — better decisions when bearing consequences"],
     ["Stoicism", "Practical Philosophy"], 0.85),
    ("Cognitive Biases and Decision Making", "psychology",
     "Understanding cognitive biases — confirmation bias, anchoring, loss aversion — enables deliberate correction in important decisions.",
     ["Confirmation bias makes us seek information that confirms existing beliefs",
      "Anchoring bias: the first number encountered disproportionately influences estimates",
      "Loss aversion makes us irrationally conservative — losses feel 2x as painful as gains"],
     ["Cognitive Biases", "Decision Science"], 0.9),
    ("Psychology of Performance and Motivation", "psychology",
     "Optimal performance requires challenge-skill balance for flow, growth mindset for resilience, and managing cognitive load.",
     ["Flow occurs when task difficulty slightly exceeds current skill level",
      "Growth mindset — believing abilities develop through effort — enables persistence",
      "Working memory holds only 4-7 items; effective instruction manages cognitive load"],
     ["Performance Psychology", "Motivation Science"], 0.85),
    ("Behavioral Psychology and Habit Science", "psychology",
     "Understanding the cue-routine-reward loop, Zeigarnik effect, and paradox of choice enables deliberate behavior design.",
     ["The cue-routine-reward cycle enables deliberate habit modification",
      "Unfinished tasks occupy working memory (Zeigarnik effect) — write them down to free cognitive resources",
      "Limiting choices to 3-5 options improves both decision speed and satisfaction"],
     ["Behavioral Psychology", "Habit Science"], 0.85),
]


def _write_note(title, domain, summary, key_points, aliases, confidence, capture_paths, captures_by_path, promoted_paths, notes_created):
    """Write a single note file and mark its source captures as promoted."""
    # Merge tags from captures
    merged_tags = set()
    for cp in capture_paths:
        cap = captures_by_path.get(cp)
        if cap:
            merged_tags.update(cap["tags"])
    merged_tags.add(domain)
    tags = sorted(merged_tags)

    # Generate note slug & filename
    slug = generate_slug(title)
    filename = f"notes/{slug}.md"
    counter = 2
    while (VAULT / filename).exists():
        filename = f"notes/{slug}-{counter}.md"
        counter += 1

    # Build note body
    points_text = "\n\n".join(
        f"{i+1}. **{point.split(' — ')[0] if ' — ' in point else point[:50]}**: {point}"
        for i, point in enumerate(key_points)
    )
    body = f"# Summary\n\n{summary}\n\n# Notes\n\n{points_text}\n\n# Links\n\n"

    now_str = datetime.now(timezone.utc).isoformat()
    metadata = {
        "title": title,
        "status": "note",
        "created": now_str,
        "updated": now_str,
        "domain": domain,
        "confidence": confidence,
        "tags": tags,
        "aliases": aliases,
        "promoted_from": capture_paths,
    }

    post = frontmatter.Post(body, **metadata)
    filepath = VAULT / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(frontmatter.dumps(post), encoding="utf-8")

    # Mark source captures as promoted
    for cap_path in capture_paths:
        promoted_paths.add(cap_path)
        cap_file = VAULT / cap_path
        if cap_file.exists():
            cap_content = cap_file.read_text(encoding="utf-8")
            cap_post = frontmatter.loads(cap_content)
            existing = cap_post.metadata.get("promoted_to") or []
            if isinstance(existing, str):
                existing = [existing]
            if filename not in existing:
                existing.append(filename)
            cap_post.metadata["promoted_to"] = existing
            cap_post.metadata["status"] = "promoted"
            cap_file.write_text(frontmatter.dumps(cap_post), encoding="utf-8")

    notes_created.append({
        "path": filename,
        "title": title,
        "domain": domain,
        "tags": tags,
        "member_captures": capture_paths,
    })


def promote_captures(captures: list[dict]) -> list[dict]:
    """Promote captures into notes. Target: ~700 promoted captures.

    Phase 1: Use hand-crafted NOTE_PLANS (45 notes, each consuming unique captures).
    Phase 2: Auto-generate additional notes from remaining unpromoted captures.
    """
    notes_created: list[dict] = []
    promoted_paths: set[str] = set()
    captures_by_path = {c["path"]: c for c in captures}

    # Build a tag-to-captures index
    tag_index: dict[str, list[dict]] = defaultdict(list)
    for cap in captures:
        for tag in cap["tags"]:
            tag_index[tag].append(cap)

    # ── Phase 1: Hand-crafted notes ──────────────────────────────────────
    for title, domain, summary, key_points, aliases, confidence in NOTE_PLANS:
        matching = [c for c in tag_index.get(domain, []) if c["path"] not in promoted_paths]
        if not matching:
            continue

        random.shuffle(matching)
        selected = matching[:random.randint(3, min(5, len(matching)))]
        capture_paths = [c["path"] for c in selected]

        _write_note(title, domain, summary, key_points, aliases, confidence,
                    capture_paths, captures_by_path, promoted_paths, notes_created)

    # ── Phase 2: Auto-generate notes from remaining captures ─────────────
    # Group unpromoted captures by their primary tag (first tag)
    TARGET_PROMOTED = 700
    remaining = [c for c in captures if c["path"] not in promoted_paths]
    random.shuffle(remaining)

    # Group by primary tag
    tag_groups: dict[str, list[dict]] = defaultdict(list)
    for cap in remaining:
        primary_tag = cap["tags"][0] if cap["tags"] else "general"
        tag_groups[primary_tag].append(cap)

    # Auto-generate notes in round-robin across tags until we hit target
    note_counter = 0
    while len(promoted_paths) < TARGET_PROMOTED:
        made_progress = False
        for tag, group in list(tag_groups.items()):
            if len(promoted_paths) >= TARGET_PROMOTED:
                break

            # Pick 3-4 unpromoted captures from this tag group
            available = [c for c in group if c["path"] not in promoted_paths]
            if len(available) < 3:
                continue

            batch_size = min(random.randint(3, 4), len(available))
            selected = available[:batch_size]
            capture_paths = [c["path"] for c in selected]

            note_counter += 1
            # Generate a descriptive title from the captures
            first_title = selected[0]["title"]
            # Use the capture title as basis, ensuring uniqueness
            auto_title = f"{first_title}"[:50]
            domain = tag
            summary = f"Synthesized insights on {tag} combining {len(selected)} related observations."
            key_points = [c["insight"][:120] for c in selected]
            aliases: list[str] = []
            confidence = round(random.uniform(0.6, 0.85), 2)

            _write_note(auto_title, domain, summary, key_points, aliases, confidence,
                        capture_paths, captures_by_path, promoted_paths, notes_created)
            made_progress = True

        if not made_progress:
            break  # No more groups with enough captures

    return notes_created


# ---------------------------------------------------------------------------
# Step 4: Auto-insert wikilinks between notes
# ---------------------------------------------------------------------------

def insert_wikilinks():
    """Re-read all notes and insert wikilinks to other notes."""
    adapter = LocalStorageAdapter(str(VAULT))
    title_cache = collect_note_titles(adapter)

    for note_file in (VAULT / "notes").glob("*.md"):
        rel_path = str(note_file.relative_to(VAULT))
        content = note_file.read_text(encoding="utf-8")
        post = frontmatter.loads(content)
        title = post.metadata.get("title", "")

        new_body, inserted = auto_insert_wikilinks(
            post.content, title_cache, exclude_titles=[title.lower()]
        )
        if inserted:
            post.content = new_body
            note_file.write_text(frontmatter.dumps(post), encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 5: Create topics from notes
# ---------------------------------------------------------------------------

TOPIC_PLANS = [
    ("AI-Assisted Development", "ai",
     "How AI tools are reshaping the software development lifecycle — from code generation to testing to review.",
     ["How will AI change the role of senior vs junior developers?",
      "What tasks should remain human-only in AI-assisted workflows?",
      "How do we evaluate AI-generated code quality at scale?"],
     ["AI Dev", "AI Tools"]),
    ("Prompt Engineering Mastery", "ai",
     "The art and science of communicating effectively with large language models through structured prompting techniques.",
     ["Will prompt engineering become a distinct professional discipline?",
      "How do prompting techniques transfer across different model architectures?",
      "What are the limits of prompt-based behavior modification?"],
     ["Prompting"]),
    ("Large Language Model Architecture", "ai",
     "The technical foundations of modern LLMs — transformers, attention mechanisms, training strategies, and inference optimization.",
     ["What architectural innovations will follow transformers?",
      "How small can effective models get with better training techniques?",
      "Will multimodal models converge to a single architecture?"],
     ["LLM Architecture"]),
    ("Personal Knowledge Management", "pkm",
     "Systems and practices for capturing, organizing, and leveraging personal knowledge across projects and over time.",
     ["How should PKM systems adapt to AI-augmented workflows?",
      "What's the right balance between capture volume and processing depth?",
      "How do you measure the ROI of a PKM system?"],
     ["PKM"]),
    ("Learning Science and Memory", "learning",
     "Evidence-based techniques for effective learning, from spaced repetition to metacognition to memory consolidation.",
     ["How can we personalize learning paths using spaced repetition data?",
      "What role does emotion play in memory formation and retrieval?",
      "How do expert and novice learning strategies differ at a neural level?"],
     ["Learning Science"]),
    ("Deep Work and Productivity Systems", "productivity",
     "Strategies for sustained cognitive performance — environment design, time management, and habit formation.",
     ["How do remote/hybrid work environments affect deep work capacity?",
      "Can AI assistants protect deep work time rather than fragment it?",
      "What productivity practices transfer across different creative disciplines?"],
     ["Productivity Systems"]),
    ("The Craft of Writing", "writing",
     "Writing as both a thinking tool and communication skill — from daily practice to technical clarity to public publishing.",
     ["How does AI change the writing process and the value of human writing?",
      "What makes technical writing effective across different expertise levels?",
      "How do constraints improve creative output?"],
     ["Writing Craft"]),
    ("Software Architecture and Design", "programming",
     "Principles for building maintainable, scalable software — from code organization to distributed systems to deployment strategies.",
     ["When should you choose microservices over a monolith?",
      "How do you balance consistency and availability in practice?",
      "What architectural patterns best support continuous deployment?"],
     ["Software Architecture"]),
    ("Software Testing and Quality", "programming",
     "Comprehensive testing strategies — TDD, property-based testing, contract testing — and their role in software quality.",
     ["What's the right ratio of unit to integration to e2e tests?",
      "How do you test AI-integrated systems effectively?",
      "What testing practices provide the highest ROI?"],
     ["Testing Strategy"]),
    ("Health Optimization for Knowledge Workers", "health",
     "Physical and mental health practices specifically tailored to the demands of intensive cognitive work.",
     ["What's the minimum effective dose of exercise for cognitive benefits?",
      "How do you build sustainable health habits in a deadline-driven culture?",
      "What role does social health play in cognitive performance?"],
     ["Knowledge Worker Health"]),
    ("Mental Models and Decision Making", "philosophy",
     "A toolkit of thinking frameworks — from Stoic philosophy to cognitive bias awareness — for better decisions under uncertainty.",
     ["Which mental models provide the most leverage across different domains?",
      "How do you train yourself to apply the right model in the right situation?",
      "Can systematic use of mental models compensate for cognitive biases?"],
     ["Mental Models", "Decision Frameworks"]),
    ("Psychology of Performance", "psychology",
     "Understanding flow states, motivation, cognitive biases, and behavioral design for sustained high performance.",
     ["How do you reliably enter flow state for creative knowledge work?",
      "What's the relationship between intrinsic motivation and skill development?",
      "How do you design environments that minimize cognitive bias impact?"],
     ["Performance Psychology"]),
]


def create_topics(notes: list[dict]) -> list[dict]:
    """Create topic files from note groups."""
    topics_created = []

    # Build domain-to-notes index
    domain_index: dict[str, list[dict]] = defaultdict(list)
    for note in notes:
        domain_index[note["domain"]].append(note)

    for title, domain, core_idea, open_questions, aliases in TOPIC_PLANS:
        matching_notes = domain_index.get(domain, [])
        if not matching_notes:
            continue

        member_note_paths = [n["path"] for n in matching_notes]
        merged_tags = set()
        for n in matching_notes:
            merged_tags.update(n["tags"])

        slug = generate_slug(title)
        filename = f"topics/{slug}.md"
        counter = 2
        while (VAULT / filename).exists():
            filename = f"topics/{slug}-{counter}.md"
            counter += 1

        # Build topic body
        key_notes_md = "\n".join(
            f"- [[{n['title']}]]" for n in matching_notes
        )
        open_q_md = "\n".join(f"- {q}" for q in open_questions)

        body = (
            f"# Topic\n\n"
            f"## Core Idea\n\n{core_idea}\n\n"
            f"## Key Notes\n\n{key_notes_md}\n\n"
            f"## Open Questions\n\n{open_q_md}\n"
        )

        now_str = datetime.now(timezone.utc).isoformat()
        metadata = {
            "title": title,
            "status": "topic",
            "created": now_str,
            "updated": now_str,
            "domain": domain,
            "tags": sorted(merged_tags),
            "aliases": aliases,
            "member_notes": member_note_paths,
            "graph_generation": 0,
        }

        post = frontmatter.Post(body, **metadata)
        filepath = VAULT / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(frontmatter.dumps(post), encoding="utf-8")

        # Add reverse references on member notes
        for note_path in member_note_paths:
            note_file = VAULT / note_path
            if note_file.exists():
                note_content = note_file.read_text(encoding="utf-8")
                note_post = frontmatter.loads(note_content)
                topics_list = note_post.metadata.get("topics", [])
                if not isinstance(topics_list, list):
                    topics_list = []
                if filename not in topics_list:
                    topics_list.append(filename)
                note_post.metadata["topics"] = topics_list
                note_file.write_text(frontmatter.dumps(note_post), encoding="utf-8")

        topics_created.append({
            "path": filename,
            "title": title,
            "domain": domain,
            "member_count": len(member_note_paths),
        })

    return topics_created


# ---------------------------------------------------------------------------
# Step 6: Build knowledge graph
# ---------------------------------------------------------------------------

def build_graph():
    """Build knowledge graph and clusters."""
    adapter = LocalStorageAdapter(str(VAULT))
    graph = VaultGraph(adapter)
    rebuild_result = graph.rebuild()

    clusters = compute_clusters(graph)
    adapter.write_file(".brain/clusters.json", clusters.model_dump_json(indent=2))

    # Stamp graph_generation on topics
    for topic_file in (VAULT / "topics").glob("*.md"):
        content = topic_file.read_text(encoding="utf-8")
        post = frontmatter.loads(content)
        post.metadata["graph_generation"] = graph.generation
        topic_file.write_text(frontmatter.dumps(post), encoding="utf-8")

    return rebuild_result, clusters


# ---------------------------------------------------------------------------
# Step 7: Generate report
# ---------------------------------------------------------------------------

def generate_report(captures, notes, topics, graph_result, clusters):
    """Print a comprehensive report."""
    # Count promoted vs unpromoted captures
    promoted = 0
    unpromoted = 0
    for cap_file in (VAULT / "captures").glob("*.md"):
        content = cap_file.read_text(encoding="utf-8")
        post = frontmatter.loads(content)
        if post.metadata.get("promoted_to"):
            promoted += 1
        else:
            unpromoted += 1

    # Domain distribution of notes
    domain_counts = Counter(n["domain"] for n in notes)

    # Tag distribution
    all_tags = Counter()
    for cap in captures:
        for tag in cap["tags"]:
            all_tags[tag] += 1

    print("=" * 60)
    print("  EXAMPLE VAULT GENERATION REPORT")
    print("=" * 60)
    print()
    print(f"  Captures:    {len(captures)}")
    print(f"    Promoted:  {promoted}")
    print(f"    Available: {unpromoted}")
    print()
    print(f"  Notes:       {len(notes)}")
    print(f"  Topics:      {len(topics)}")
    print()
    print("  Graph Statistics:")
    print(f"    Nodes:     {graph_result.get('nodes', 0)}")
    print(f"    Edges:     {graph_result.get('edges', 0)}")
    print(f"    Clusters:  {len(clusters.clusters)}")
    print()
    print("  Domain Distribution (Notes):")
    for domain, count in sorted(domain_counts.items()):
        print(f"    {domain:20s} {count}")
    print()
    print("  Tag Distribution (Captures, top 15):")
    for tag, count in all_tags.most_common(15):
        bar = "#" * (count // 10)
        print(f"    {tag:20s} {count:4d} {bar}")
    print()
    print("  Sample Topic:")
    if topics:
        t = topics[0]
        print(f"    Title:   {t['title']}")
        print(f"    Domain:  {t['domain']}")
        print(f"    Members: {t['member_count']} notes")
    print()
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Clearing existing vault content...")
    clear_vault()

    print(f"Generating 1000 captures from {len(CAPTURES)} unique insights...")
    captures = generate_captures()
    print(f"  Created {len(captures)} captures")

    print(f"Promoting captures into {len(NOTE_PLANS)} notes...")
    notes = promote_captures(captures)
    print(f"  Created {len(notes)} notes")

    print("Inserting wikilinks between notes...")
    insert_wikilinks()

    print(f"Creating {len(TOPIC_PLANS)} topics...")
    topics = create_topics(notes)
    print(f"  Created {len(topics)} topics")

    print("Building knowledge graph...")
    graph_result, clusters = build_graph()
    print(f"  Graph: {graph_result.get('nodes', 0)} nodes, {graph_result.get('edges', 0)} edges")
    print(f"  Clusters: {len(clusters.clusters)}")

    print()
    generate_report(captures, notes, topics, graph_result, clusters)


if __name__ == "__main__":
    main()
