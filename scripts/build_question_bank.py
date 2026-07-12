# -*- coding: utf-8 -*-
"""
build_question_bank.py — generate a 5,000+ real interview-question bank.

Output: question_bank.json in the exact shape ai_assistant.py expects:
    { "<topic>": { "Junior (0-2 yrs)": ["1. ...", ...],
                   "Mid (2-5 yrs)":    ["1. ...", ...],
                   "Senior (5+ yrs)":  ["1. ...", ...] } }

Method: each topic carries real, specific data — concepts, comparison pairs,
production scenarios, design prompts, and (for DSA) coding problems. These are
expanded through difficulty-appropriate question templates, deduplicated, and
capped per level. This mirrors how real interviewers vary a finite set of
concepts into many phrasings.
"""

import json
import random

random.seed(42)  # deterministic output

JUNIOR = "Junior (0-2 yrs)"
MID = "Mid (2-5 yrs)"
SENIOR = "Senior (5+ yrs)"
PER_LEVEL = 20  # target per topic per level  (94 topics * 3 * 20 ≈ 5,640)

# ── Templates. {c}=concept {a}/{b}=pair {s}=scenario {d}=design {p}=problem ──
T_JUNIOR = [
    "What is {c}, and why is it used?",
    "Explain {c} in simple terms, with an example.",
    "What are the main features or benefits of {c}?",
    "When would you use {c} in a real project?",
    "What problem does {c} solve?",
]
T_JUNIOR_PAIR = [
    "What is the difference between {a} and {b}?",
    "When would you use {a} instead of {b}?",
    "Compare {a} and {b} with a quick example of each.",
]
T_MID = [
    "How does {c} work under the hood?",
    "What are common pitfalls with {c}, and how do you avoid them?",
    "How would you test {c}?",
    "What are the performance implications of {c}?",
    "How would you explain {c} to a junior developer, including edge cases?",
]
T_MID_PAIR = [
    "When would you choose {a} over {b}? What are the tradeoffs?",
    "How do {a} and {b} differ in terms of performance and use case?",
]
T_MID_SCEN = [
    "You're seeing {s}. How would you investigate and fix it?",
    "A teammate reports {s}. Walk through your debugging steps.",
]
T_SENIOR = [
    "How would you scale and optimize {c} for high load in production?",
    "How would you make {c} highly available and fault-tolerant?",
    "What are the failure modes of {c} at scale, and how do you guard against them?",
    "How would you monitor and set alerts for {c} in production?",
]
T_SENIOR_PAIR = [
    "Compare {a} and {b} at scale — what breaks first and why?",
    "In a high-throughput system, how do you decide between {a} and {b}?",
]
T_SENIOR_SCEN = [
    "Production incident: {s}. Walk me through your diagnosis and response.",
    "At 2am you're paged for {s}. What are your first steps and how do you prevent a repeat?",
]
T_SENIOR_DESIGN = [
    "Design {d}. Walk through your key decisions and tradeoffs.",
    "Design {d}. How would you handle scale, failures, and data consistency?",
]
T_PROB = [
    "Implement: {p}. Then discuss time and space complexity.",
    "Solve: {p}. Start with brute force, then optimize.",
    "Coding: {p}. Explain your approach before writing code.",
]

# ── Per-topic data. Compact but real and specific. ──
# c=concepts, p=pairs, s=scenarios, d=designs, prob=coding problems
D = {}

def add(topic, c=None, p=None, s=None, d=None, prob=None):
    D[topic] = {"c": c or [], "p": p or [], "s": s or [], "d": d or [], "prob": prob or []}

# ---------------- JAVA ----------------
add("Core Java",
    c=["the JVM", "the JIT compiler", "autoboxing", "the `String` pool", "garbage collection",
       "the `equals()`/`hashCode()` contract", "immutability", "pass-by-value semantics",
       "`static` vs instance members", "the `final` keyword", "varargs", "enums"],
    p=[("`==`", "`.equals()`"), ("`ArrayList`", "`LinkedList`"), ("`String`", "`StringBuilder`"),
       ("checked", "unchecked exceptions"), ("`final`, `finally`", "`finalize`"),
       ("an interface", "an abstract class"), ("`HashMap`", "`Hashtable`")],
    s=["intermittent `NullPointerException`s under load", "`OutOfMemoryError` after a few hours",
       "a `ConcurrentModificationException` while iterating"],
    d=["an immutable value object used as a map key", "a simple object pool"])
add("OOP & Design Patterns",
    c=["encapsulation", "polymorphism", "the Singleton pattern", "the Factory pattern",
       "the Strategy pattern", "the Observer pattern", "the Builder pattern",
       "the SOLID principles", "composition over inheritance", "the Decorator pattern"],
    p=[("composition", "inheritance"), ("the Factory", "the Abstract Factory pattern"),
       ("the Strategy", "the State pattern"), ("an interface", "an abstract class")],
    s=["a class that keeps growing new responsibilities", "tight coupling that blocks testing"],
    d=["a plugin system using the Strategy pattern", "a notification system using Observer",
       "a thread-safe Singleton"])
add("Collections & Generics",
    c=["the `Collection` hierarchy", "generics and type erasure", "the `Comparable` interface",
       "`Comparator`", "`fail-fast` iterators", "bounded type parameters", "wildcards (`? extends`)"],
    p=[("`HashMap`", "`TreeMap`"), ("`HashSet`", "`LinkedHashSet`"), ("`List`", "`Set`"),
       ("`Comparable`", "`Comparator`"), ("`Iterator`", "`ListIterator`")],
    s=["a `ClassCastException` from a raw type", "poor lookup performance in a large `HashMap`"],
    d=["an LRU cache using `LinkedHashMap`"])
add("Multithreading & Concurrency",
    c=["the `synchronized` keyword", "`volatile`", "the `java.util.concurrent` package",
       "a `ReentrantLock`", "`ThreadLocal`", "the `ExecutorService`", "a `CountDownLatch`",
       "atomic variables", "the fork/join framework"],
    p=[("`synchronized`", "`ReentrantLock`"), ("`wait()`/`notify()`", "a `BlockingQueue`"),
       ("`volatile`", "`synchronized`"), ("a thread pool", "creating threads directly")],
    s=["a deadlock between two locks", "a race condition on a shared counter",
       "threads stuck waiting forever"],
    d=["a thread-safe bounded producer-consumer queue", "a rate limiter shared across threads"])
add("JVM & Memory Management",
    c=["the heap and stack", "garbage collection generations", "the G1 collector",
       "escape analysis", "metaspace", "class loading", "JVM flags for tuning"],
    p=[("young", "old generation"), ("the stack", "the heap"), ("G1", "ZGC")],
    s=["frequent full-GC pauses", "a slow memory leak over days", "rising latency under load"],
    d=["GC tuning for a low-latency trading service"])
add("Spring Boot",
    c=["auto-configuration", "starters", "the embedded server", "`application.yml` profiles",
       "actuator endpoints", "dependency injection", "`@RestController`"],
    p=[("`@Component`", "`@Service`"), ("`@RequestParam`", "`@PathVariable`"),
       ("constructor", "field injection")],
    s=["a slow first request (cold start)", "a bean that fails to autowire",
       "an endpoint returning 500 with no useful log"],
    d=["a resilient REST service with retries and timeouts", "a health-check and readiness setup"])
add("Java 8+ (Streams, Lambdas)",
    c=["lambda expressions", "the `Stream` API", "`Optional`", "method references",
       "functional interfaces", "`Collectors`", "the `CompletableFuture` API", "default methods"],
    p=[("`map`", "`flatMap`"), ("a `Stream`", "a `Collection`"), ("`findFirst`", "`findAny`"),
       ("intermediate", "terminal operations")],
    s=["a stream that never terminates", "a `NullPointerException` inside a stream pipeline"],
    d=["a parallel data-processing pipeline with `CompletableFuture`"])
add("Exception Handling",
    c=["checked vs unchecked exceptions", "the `try-with-resources` statement", "custom exceptions",
       "exception chaining", "the `finally` block", "global exception handling"],
    p=[("checked", "unchecked exceptions"), ("`throw`", "`throws`"),
       ("catching `Exception`", "catching specific types")],
    s=["swallowed exceptions hiding a real bug", "resource leaks from unclosed streams"],
    d=["a consistent error-handling strategy for a REST API"])
add("Data Structures & Algorithms (Java)",
    c=["`ArrayDeque`", "`PriorityQueue`", "`TreeMap` internals (red-black tree)",
       "hashing in `HashMap`", "the `Collections` utility methods"],
    p=[("`ArrayList`", "`LinkedList`"), ("`Stack`", "`ArrayDeque`"), ("array", "`ArrayList`")],
    s=["O(n) lookups where O(1) was expected"],
    prob=["find the first non-repeating character in a string",
          "detect a cycle in a linked list", "implement an LRU cache"])
add("Microservices",
    c=["service boundaries", "an API gateway", "service discovery", "the circuit breaker pattern",
       "distributed tracing", "the saga pattern", "the outbox pattern", "idempotency keys"],
    p=[("a monolith", "microservices"), ("orchestration", "choreography"),
       ("sync (REST)", "async (messaging)"), ("the saga", "a two-phase commit")],
    s=["cascading failures when one service is slow", "duplicate side effects from retried requests",
       "a request that mysteriously touches eight services"],
    d=["an event-driven order-processing system", "a payment service with idempotent APIs"])
add("System Design",
    c=["load balancing", "caching layers", "database replication", "sharding", "message queues",
       "the CAP theorem", "consistent hashing", "rate limiting"],
    p=[("horizontal", "vertical scaling"), ("SQL", "NoSQL"), ("cache-aside", "write-through caching"),
       ("strong", "eventual consistency")],
    s=["a hot partition overloading one shard", "cache stampede after a deploy"],
    d=["a URL shortener", "a news feed with fan-out", "a globally distributed chat system",
       "a distributed rate limiter"])
add("DSA Problems",
    c=["Big-O analysis", "the two-pointer technique", "sliding windows", "hashing for O(1) lookups"],
    p=[("BFS", "DFS"), ("recursion", "iteration"), ("`O(n log n)`", "`O(n^2)` sorting")],
    prob=["Two Sum", "reverse a linked list", "check for balanced parentheses",
          "merge two sorted arrays", "find the median of two sorted arrays",
          "longest substring without repeating characters", "serialize and deserialize a binary tree"])
add("Mixed / Full Stack Java",
    c=["REST API design", "JPA/Hibernate", "connection pooling", "JWT authentication",
       "the N+1 query problem", "DTOs vs entities"],
    p=[("REST", "GraphQL"), ("optimistic", "pessimistic locking"), ("JPA", "raw JDBC")],
    s=["the N+1 query problem slowing an endpoint", "a connection-pool exhaustion under load"],
    d=["a full-stack CRUD app with pagination and auth"])

# ---------------- PYTHON ----------------
add("Core Python",
    c=["the GIL", "list comprehensions", "generators", "decorators", "context managers",
       "duck typing", "the `__name__ == '__main__'` idiom", "`*args`/`**kwargs`", "closures"],
    p=[("a list", "a tuple"), ("`is`", "`==`"), ("a list", "a set"),
       ("`@staticmethod`", "`@classmethod`"), ("a shallow", "a deep copy")],
    s=["a mutable-default-argument bug", "a `UnicodeDecodeError` reading a file"],
    d=["a retry decorator with backoff"])
add("OOP in Python",
    c=["dunder methods", "the MRO (method resolution order)", "`@property`", "abstract base classes",
       "`__slots__`", "multiple inheritance", "metaclasses"],
    p=[("`@staticmethod`", "`@classmethod`"), ("composition", "inheritance"),
       ("`__str__`", "`__repr__`")],
    s=["a diamond-inheritance conflict", "unexpected shared state across instances"],
    d=["a plugin registry using metaclasses"])
add("Data Structures (Python)",
    c=["`collections.deque`", "`heapq`", "`defaultdict`", "`Counter`", "named tuples",
       "the `dict` implementation (open addressing)"],
    p=[("a list", "a `deque`"), ("a `dict`", "an `OrderedDict`"), ("a set", "a frozenset")],
    prob=["find the top-k frequent elements", "implement an LRU cache with `OrderedDict`"])
add("Python Libraries (NumPy/Pandas)",
    c=["NumPy broadcasting", "vectorization", "a Pandas `DataFrame`", "`groupby` aggregation",
       "the `apply` method", "handling missing data", "merge/join in Pandas"],
    p=[("a NumPy array", "a Python list"), ("`loc`", "`iloc`"), ("`merge`", "`concat`"),
       ("`apply`", "vectorized operations")],
    s=["a Pandas pipeline running out of memory", "a slow `apply` over millions of rows"],
    d=["a memory-efficient ETL over a 10GB CSV"])
add("Django / Flask",
    c=["the Django ORM", "middleware", "migrations", "the request/response cycle",
       "Flask blueprints", "template rendering", "CSRF protection"],
    p=[("Django", "Flask"), ("`select_related`", "`prefetch_related`"),
       ("function-based", "class-based views")],
    s=["the N+1 query problem in the ORM", "a slow endpoint under concurrent requests"],
    d=["a REST API with authentication and pagination"])
add("Python for ML/AI",
    c=["train/test split", "overfitting", "cross-validation", "feature scaling",
       "the bias-variance tradeoff", "a confusion matrix", "gradient descent"],
    p=[("classification", "regression"), ("precision", "recall"), ("L1", "L2 regularization"),
       ("bagging", "boosting")],
    s=["a model with 99% train accuracy but poor test accuracy", "data leakage inflating metrics"],
    d=["a training-and-evaluation pipeline with reproducible metrics"])
add("Async & Concurrency",
    c=["the event loop", "`async`/`await`", "coroutines", "`asyncio.gather`", "the GIL's effect",
       "thread pools", "process pools"],
    p=[("`asyncio`", "threading"), ("threading", "multiprocessing"),
       ("concurrency", "parallelism"), ("a coroutine", "a thread")],
    s=["an async function that blocks the event loop", "a program that doesn't speed up with threads"],
    d=["a service handling 10k concurrent connections"])
add("Testing in Python",
    c=["unit vs integration tests", "`pytest` fixtures", "mocking", "parametrized tests",
       "test coverage", "`monkeypatch`", "the AAA (arrange-act-assert) pattern"],
    p=[("a mock", "a stub"), ("`unittest`", "`pytest`"), ("unit", "integration tests")],
    s=["a flaky test that fails intermittently", "tests that pass locally but fail in CI"],
    d=["a test strategy for a service with external API calls"])

# ---------------- DEVOPS ----------------
add("CI/CD Pipelines",
    c=["a build stage", "artifact management", "pipeline-as-code", "deployment gates",
       "environment promotion", "rollback strategy", "secrets in pipelines"],
    p=[("CI", "CD"), ("blue-green", "canary deployment"), ("a pipeline stage", "a job")],
    s=["a flaky pipeline that fails randomly", "a deploy that half-succeeded and left mixed versions"],
    d=["a CI/CD pipeline for a fleet of microservices with independent releases"])
add("Docker & Containers",
    c=["images vs containers", "layers and caching", "multi-stage builds", "volumes",
       "networking modes", "`CMD` vs `ENTRYPOINT`", "the container runtime"],
    p=[("an image", "a container"), ("`CMD`", "`ENTRYPOINT`"), ("`COPY`", "`ADD`"),
       ("a container", "a VM")],
    s=["a container that exits immediately", "an image that's several GB too large"],
    d=["a minimal, secure production image for a Java/Python app"])
add("Kubernetes (K8s)",
    c=["pods", "deployments", "services", "ingress", "config maps and secrets",
       "liveness/readiness probes", "the scheduler", "horizontal pod autoscaling", "namespaces"],
    p=[("a deployment", "a statefulset"), ("a service", "an ingress"),
       ("a config map", "a secret"), ("a liveness", "a readiness probe")],
    s=["a pod stuck in CrashLoopBackOff", "a pod stuck in Pending", "an OOMKilled container"],
    d=["a zero-downtime rolling deployment", "autoscaling for a spiky workload"])
add("Terraform & IaC",
    c=["Terraform state", "providers", "modules", "the plan/apply cycle", "remote backends",
       "state locking", "workspaces", "drift detection"],
    p=[("Terraform", "CloudFormation"), ("`count`", "`for_each`"), ("local", "remote state")],
    s=["state drift after a manual console change", "two engineers corrupting shared state"],
    d=["a reusable module structure for multi-environment infra"])
add("Jenkins / GitLab CI",
    c=["a Jenkinsfile", "declarative vs scripted pipelines", "agents/runners", "shared libraries",
       "GitLab CI stages", "pipeline caching", "parallel jobs"],
    p=[("declarative", "scripted pipelines"), ("Jenkins", "GitLab CI")],
    s=["a build that's slow because nothing is cached", "a runner that keeps running out of disk"],
    d=["a scalable runner setup for a large monorepo"])
add("Monitoring & Logging",
    c=["metrics vs logs vs traces", "the RED/USE method", "structured logging", "alerting rules",
       "SLIs and SLOs", "dashboards", "log aggregation"],
    p=[("metrics", "logs"), ("a metric", "a trace"), ("Prometheus", "the ELK stack")],
    s=["an alert storm during an incident", "logs that are useless because they're unstructured"],
    d=["an observability stack (logs, metrics, traces) for 50 microservices"])
add("Linux & Shell Scripting",
    c=["file permissions", "pipes and redirection", "processes and signals", "cron jobs",
       "environment variables", "`grep`/`awk`/`sed`", "the `/proc` filesystem"],
    p=[("a hard link", "a symlink"), ("`>`", "`>>`"), ("a process", "a thread")],
    s=["a server running out of disk with no obvious cause", "a runaway process pegging CPU"],
    d=["a log-rotation and cleanup script with alerting"])
add("Git & Version Control",
    c=["the staging area", "branching strategies", "rebasing", "cherry-picking", "the reflog",
       "submodules", "hooks"],
    p=[("`merge`", "`rebase`"), ("`reset`", "`revert`"), ("`fetch`", "`pull`")],
    s=["a force-push that erased a teammate's work", "a merge conflict in a binary file"],
    d=["a branching and release strategy for a team of 30"])

# ---------------- AWS ----------------
add("EC2 & VPC",
    c=["instance types", "security groups", "subnets", "route tables", "elastic IPs",
       "auto scaling groups", "NAT gateways", "placement groups"],
    p=[("a security group", "a NACL"), ("a public", "a private subnet"),
       ("EC2", "Fargate"), ("a NAT gateway", "an internet gateway")],
    s=["an instance that can't reach the internet", "a security group blocking legitimate traffic"],
    d=["a highly available multi-AZ VPC network"])
add("S3 & Storage",
    c=["storage classes", "bucket policies", "versioning", "lifecycle rules", "server-side encryption",
       "pre-signed URLs", "S3 event notifications"],
    p=[("S3 Standard", "Glacier"), ("a bucket policy", "an IAM policy"), ("S3", "EBS")],
    s=["an accidentally public bucket", "slow uploads of very large files"],
    d=["a secure, cost-optimized storage tier for logs and backups"])
add("Lambda & Serverless",
    c=["cold starts", "concurrency limits", "event sources", "the execution role", "layers",
       "step functions", "provisioned concurrency"],
    p=[("Lambda", "EC2"), ("Lambda", "Fargate"), ("synchronous", "asynchronous invocation")],
    s=["cold starts hurting p99 latency", "a Lambda being throttled under a spike"],
    d=["a serverless REST API with a queue buffer"])
add("RDS & DynamoDB",
    c=["read replicas", "Multi-AZ failover", "DynamoDB partition keys", "global secondary indexes",
       "DynamoDB capacity modes", "connection pooling for RDS", "point-in-time recovery"],
    p=[("RDS", "DynamoDB"), ("a partition key", "a sort key"), ("provisioned", "on-demand capacity")],
    s=["a hot partition in DynamoDB", "RDS connection exhaustion from Lambda"],
    d=["a data layer that stays fast at 100k writes/sec"])
add("IAM & Security",
    c=["IAM roles", "policies", "the principle of least privilege", "assume-role", "MFA",
       "resource-based policies", "temporary credentials (STS)"],
    p=[("an IAM role", "an IAM user"), ("an identity", "a resource policy"),
       ("a managed", "an inline policy")],
    s=["an over-permissioned role in production", "leaked long-lived access keys"],
    d=["least-privilege access for a team of developers"])
add("AWS Architecture Design",
    c=["multi-AZ vs multi-region", "the Well-Architected Framework", "cost optimization",
       "disaster recovery (RTO/RPO)", "edge caching with CloudFront", "decoupling with SQS"],
    p=[("multi-AZ", "multi-region"), ("SQS", "SNS"), ("CloudFront", "a regional cache")],
    s=["a doubled monthly bill with no traffic change", "a single-AZ dependency causing an outage"],
    d=["a highly available, auto-scaling web platform", "a DR strategy with a 15-minute RTO"])
add("EKS & ECS",
    c=["the control plane", "node groups", "Fargate profiles", "task definitions", "the ALB ingress",
       "IRSA (IAM roles for service accounts)"],
    p=[("EKS", "ECS"), ("EC2 launch type", "Fargate launch type")],
    s=["pods that can't pull an image from ECR", "a task that keeps getting killed"],
    d=["a container platform with autoscaling and secure secrets"])
add("CloudFormation & CDK",
    c=["stacks", "change sets", "nested stacks", "drift detection", "the CDK construct model",
       "cross-stack references"],
    p=[("CloudFormation", "the CDK"), ("CloudFormation", "Terraform")],
    s=["a stack stuck in ROLLBACK", "drift after a manual change"],
    d=["a reusable CDK construct library for standard services"])

# ---------------- KAFKA ----------------
add("Kafka Architecture",
    c=["brokers", "the commit log", "the controller", "ISR (in-sync replicas)", "leader election",
       "ZooKeeper vs KRaft", "log retention"],
    p=[("a topic", "a partition"), ("ZooKeeper", "KRaft"), ("Kafka", "a traditional queue")],
    s=["under-replicated partitions after a broker dies", "growing consumer lag"],
    d=["a Kafka cluster sized for 1M events/sec"])
add("Topics & Partitions",
    c=["partitioning strategy", "the partition key", "ordering guarantees", "replication factor",
       "log compaction", "retention policy"],
    p=[("more", "fewer partitions"), ("keyed", "round-robin partitioning"),
       ("compaction", "deletion retention")],
    s=["a hot partition from a skewed key", "message ordering breaking after a repartition"],
    d=["a partitioning scheme that preserves per-user ordering at scale"])
add("Producers & Consumers",
    c=["consumer groups", "offsets", "acks (0/1/all)", "the rebalance protocol", "idempotent producers",
       "at-least-once vs exactly-once", "manual vs auto commit"],
    p=[("at-least-once", "exactly-once"), ("auto", "manual offset commit"),
       ("`acks=1`", "`acks=all`")],
    s=["duplicate message processing after a rebalance", "consumer lag that never catches up"],
    d=["an exactly-once processing pipeline"])
add("Kafka Streams",
    c=["KStream vs KTable", "windowing", "stateful operations", "the state store", "joins",
       "exactly-once semantics", "the processor topology"],
    p=[("a KStream", "a KTable"), ("tumbling", "hopping windows"),
       ("Kafka Streams", "a consumer app")],
    s=["a state store growing unbounded", "late-arriving events breaking a window aggregation"],
    d=["a real-time sessionization pipeline"])
add("Kafka Connect",
    c=["source vs sink connectors", "converters", "SMTs (single message transforms)",
       "the dead-letter queue", "distributed mode", "offset management"],
    p=[("a source", "a sink connector"), ("standalone", "distributed mode")],
    s=["a connector stuck retrying a poison message", "schema mismatch failing a sink"],
    d=["a CDC pipeline from a database into Kafka"])
add("Schema Registry",
    c=["Avro schemas", "schema evolution", "compatibility modes", "the subject naming strategy",
       "schema IDs in messages"],
    p=[("backward", "forward compatibility"), ("Avro", "JSON Schema"), ("Avro", "Protobuf")],
    s=["a producer breaking consumers with a schema change", "a compatibility check blocking a deploy"],
    d=["a schema-governance process for many teams"])
add("Kafka Security",
    c=["TLS encryption", "SASL authentication", "ACLs", "encryption in transit vs at rest",
       "principal mapping"],
    p=[("SASL/PLAIN", "SASL/SCRAM"), ("SSL", "SASL")],
    s=["a consumer denied by an ACL", "plaintext traffic on an internal cluster"],
    d=["end-to-end security for a multi-tenant cluster"])
add("Kafka Tuning & Ops",
    c=["batch size and linger", "compression", "partition rebalancing", "log segment sizing",
       "monitoring lag", "broker JVM tuning"],
    p=[("throughput", "latency tuning"), ("gzip", "lz4 compression")],
    s=["high producer latency spikes", "uneven load across brokers after scaling"],
    d=["a tuning plan to hit sub-10ms p99 at high throughput"])

# ---------------- MICROSERVICES (dedicated mode) ----------------
add("Microservices Architecture",
    c=["bounded contexts", "the database-per-service pattern", "an API gateway", "the BFF pattern",
       "service mesh", "the strangler-fig migration"],
    p=[("a monolith", "microservices"), ("a shared", "a per-service database"),
       ("a library", "a service")],
    s=["a distributed monolith with tangled dependencies", "chatty inter-service calls hurting latency"],
    d=["decomposing a monolith incrementally without a rewrite"])
add("API Gateway",
    c=["routing", "rate limiting", "authentication offload", "request aggregation", "response caching",
       "the BFF pattern"],
    p=[("an API gateway", "a load balancer"), ("gateway auth", "per-service auth")],
    s=["the gateway becoming a single point of failure", "a slow gateway adding latency to every call"],
    d=["a highly available API gateway layer"])
add("Service Discovery",
    c=["client-side vs server-side discovery", "a service registry", "health checks", "DNS-based discovery",
       "self-registration"],
    p=[("client-side", "server-side discovery"), ("Eureka", "Consul")],
    s=["stale registry entries routing to dead instances", "a registry outage taking down routing"],
    d=["resilient service discovery for hundreds of instances"])
add("Circuit Breaker Pattern",
    c=["the closed/open/half-open states", "failure thresholds", "fallbacks", "bulkheads",
       "timeouts and retries", "Resilience4j"],
    p=[("a circuit breaker", "a retry"), ("a timeout", "a circuit breaker"),
       ("a bulkhead", "a circuit breaker")],
    s=["cascading failure when a downstream service is slow", "retries amplifying an outage"],
    d=["resilience patterns for a service with flaky dependencies"])
add("Event-Driven Architecture",
    c=["event sourcing", "the pub/sub model", "eventual consistency", "the outbox pattern",
       "idempotent consumers", "event schemas"],
    p=[("orchestration", "choreography"), ("an event", "a command"),
       ("event sourcing", "CRUD")],
    s=["a dual-write bug losing events", "out-of-order events corrupting state"],
    d=["an event-driven order system with the outbox pattern"])
add("Saga Pattern",
    c=["choreography-based sagas", "orchestration-based sagas", "compensating transactions",
       "the saga log", "idempotency"],
    p=[("a saga", "a two-phase commit"), ("orchestrated", "choreographed sagas")],
    s=["a saga stuck half-completed after a crash", "compensation that itself fails"],
    d=["a booking flow (flight+hotel+car) as a saga"])
add("Distributed Tracing",
    c=["trace and span context", "context propagation", "sampling", "OpenTelemetry",
       "correlation IDs", "the critical path"],
    p=[("a trace", "a log"), ("head", "tail sampling")],
    s=["a broken trace where spans don't connect", "one slow span buried in a 12-service request"],
    d=["end-to-end tracing across sync and async boundaries"])
add("gRPC & REST APIs",
    c=["Protocol Buffers", "streaming RPCs", "HTTP/2 multiplexing", "status codes", "deadlines",
       "backward-compatible schema evolution"],
    p=[("gRPC", "REST"), ("Protobuf", "JSON"), ("unary", "streaming RPC")],
    s=["a breaking change to a proto field", "a client ignoring deadlines and piling up calls"],
    d=["a versioned gRPC API used by many teams"])

# ---------------- SPRING (dedicated mode) ----------------
add("Spring Core & DI",
    c=["the IoC container", "bean scopes", "the bean lifecycle", "`@Autowired` resolution",
       "`@Configuration` classes", "circular dependency handling", "profiles"],
    p=[("constructor", "field injection"), ("singleton", "prototype scope"),
       ("`@Component`", "`@Bean`")],
    s=["a circular dependency at startup", "the wrong bean injected among several candidates"],
    d=["a clean configuration structure for multiple environments"])
add("Spring MVC",
    c=["the `DispatcherServlet`", "handler mapping", "`@RestController`", "content negotiation",
       "exception handlers", "interceptors", "validation"],
    p=[("`@Controller`", "`@RestController`"), ("`@RequestParam`", "`@PathVariable`"),
       ("a filter", "an interceptor")],
    s=["a 415 Unsupported Media Type error", "validation errors returning ugly 500s"],
    d=["a consistent REST error-response format"])
add("Spring Data JPA",
    c=["repositories", "derived query methods", "`@Query`", "entity relationships", "fetch types",
       "the persistence context", "transactions"],
    p=[("`FetchType.LAZY`", "`FetchType.EAGER`"), ("`save`", "`saveAndFlush`"),
       ("JPA", "raw JDBC")],
    s=["the N+1 query problem", "a `LazyInitializationException` outside a transaction"],
    d=["an efficient data layer avoiding N+1 with pagination"])
add("Spring Security",
    c=["the filter chain", "authentication vs authorization", "JWT", "OAuth2", "method security",
       "CSRF protection", "password encoding"],
    p=[("authentication", "authorization"), ("a session", "a JWT"), ("OAuth2", "basic auth")],
    s=["a JWT that never expires being replayed", "CORS blocking a legitimate frontend"],
    d=["stateless JWT auth with refresh tokens"])
add("Spring Cloud",
    c=["config server", "the gateway", "circuit breakers", "load balancing", "distributed config",
       "service registry integration"],
    p=[("Spring Cloud Gateway", "Zuul"), ("client-side", "server-side load balancing")],
    s=["a config change not propagating to services", "the gateway timing out downstream"],
    d=["a Spring Cloud setup for a dozen services"])
add("Spring Boot Testing",
    c=["`@SpringBootTest`", "slice tests (`@WebMvcTest`)", "MockMvc", "Testcontainers",
       "mocking beans", "test profiles"],
    p=[("`@SpringBootTest`", "`@WebMvcTest`"), ("a unit", "an integration test"),
       ("a mock", "Testcontainers")],
    s=["slow tests that boot the whole context", "tests passing locally but failing in CI"],
    d=["a fast, reliable test pyramid for a Spring service"])
add("Spring Actuator & Monitoring",
    c=["health endpoints", "metrics via Micrometer", "custom health indicators", "readiness/liveness",
       "distributed tracing hooks", "exposing Prometheus metrics"],
    p=[("liveness", "readiness"), ("a health check", "a metric")],
    s=["a service reporting healthy while failing requests", "missing metrics for a key endpoint"],
    d=["production-grade health and metrics for Kubernetes"])
add("Spring Batch",
    c=["jobs and steps", "chunk-oriented processing", "readers/processors/writers", "restartability",
       "partitioning", "skip and retry policies"],
    p=[("chunk", "tasklet processing"), ("single-threaded", "partitioned steps")],
    s=["a batch job that can't restart after failure", "a job running out of memory on a big file"],
    d=["a restartable nightly batch over 50M records"])

# ---------------- AI AGENTS ----------------
add("LLM Fundamentals",
    c=["tokens and tokenization", "the context window", "temperature and sampling", "embeddings",
       "the transformer/attention mechanism", "hallucination", "system vs user prompts"],
    p=[("a base", "an instruction-tuned model"), ("temperature 0", "temperature 1"),
       ("tokens", "words")],
    s=["a model confidently hallucinating facts", "responses cut off by the context limit"],
    d=["an evaluation harness to measure model quality"])
add("Prompt Engineering",
    c=["few-shot prompting", "chain-of-thought", "structured output", "system prompts",
       "prompt injection", "output parsing", "prompt templates"],
    p=[("zero-shot", "few-shot"), ("chain-of-thought", "direct answering")],
    s=["a prompt that works until inputs get long", "a user overriding your instructions"],
    d=["a robust prompt with structured JSON output and validation"])
add("RAG (Retrieval Augmented Generation)",
    c=["chunking strategy", "embeddings", "vector search", "reranking", "context injection",
       "hybrid search", "retrieval evaluation"],
    p=[("RAG", "fine-tuning"), ("keyword", "semantic search"), ("small", "large chunks")],
    s=["retrieval returning irrelevant chunks", "the model ignoring the retrieved context"],
    d=["a production RAG pipeline over millions of documents"])
add("Vector Databases",
    c=["embeddings", "ANN indexes (HNSW)", "similarity metrics", "metadata filtering",
       "recall vs latency", "index rebuilding"],
    p=[("cosine", "dot-product similarity"), ("HNSW", "IVF indexes"),
       ("a vector DB", "a keyword index")],
    s=["poor recall on semantic search", "slow queries as the index grows"],
    d=["a vector store serving low-latency search at scale"])
add("LangChain / LlamaIndex",
    c=["chains", "agents and tools", "memory", "retrievers", "output parsers", "callbacks"],
    p=[("a chain", "an agent"), ("LangChain", "LlamaIndex"), ("buffer", "summary memory")],
    s=["an agent looping without finishing", "a tool call failing on malformed arguments"],
    d=["a multi-tool agent with guardrails and retries"])
add("AI Agent Design",
    c=["the ReAct loop", "tool calling", "planning", "memory", "guardrails", "human-in-the-loop",
       "multi-agent handoff"],
    p=[("an agent", "a chatbot"), ("single-agent", "multi-agent"), ("a tool", "a prompt")],
    s=["an agent stuck in an infinite loop burning tokens", "a tool with side effects called twice"],
    d=["a multi-agent system with task handoff and coordination",
       "guardrails for an agent that can send email or make payments"])
add("Fine-tuning & RLHF",
    c=["supervised fine-tuning", "LoRA/PEFT", "RLHF", "reward models", "catastrophic forgetting",
       "dataset curation"],
    p=[("fine-tuning", "prompting"), ("full", "LoRA fine-tuning"), ("SFT", "RLHF")],
    s=["a fine-tuned model regressing on general tasks", "reward hacking during RLHF"],
    d=["a fine-tuning pipeline with evaluation and rollback"])
add("MLOps",
    c=["model versioning", "feature stores", "model monitoring", "data/concept drift", "A/B testing",
       "CI/CD for models", "shadow deployment"],
    p=[("data", "concept drift"), ("batch", "online inference"), ("shadow", "canary deploys")],
    s=["a model silently degrading from data drift", "training/serving skew"],
    d=["an ML platform with automated retraining and monitoring"])

# ---------------- SQL ----------------
add("SQL Basics & Queries",
    c=["`GROUP BY`", "aggregate functions", "`DISTINCT`", "`ORDER BY`", "`LIMIT`/`OFFSET`",
       "`CASE` expressions", "`NULL` handling"],
    p=[("`WHERE`", "`HAVING`"), ("`UNION`", "`UNION ALL`"), ("`DELETE`", "`TRUNCATE`")],
    prob=["find the second-highest salary", "find duplicate rows", "get the top N per group"])
add("Joins & Subqueries",
    c=["inner/outer joins", "self joins", "cross joins", "correlated subqueries", "CTEs",
       "`EXISTS` vs `IN`"],
    p=[("an `INNER JOIN`", "a `LEFT JOIN`"), ("a subquery", "a JOIN"), ("`EXISTS`", "`IN`"),
       ("a CTE", "a subquery")],
    s=["a join producing unexpected duplicate rows", "a correlated subquery running per row"],
    prob=["list customers with no orders", "find employees earning more than their manager"])
add("Indexing & Performance",
    c=["B-tree indexes", "composite indexes", "covering indexes", "the query planner",
       "`EXPLAIN` plans", "index selectivity", "when indexes hurt writes"],
    p=[("a clustered", "a non-clustered index"), ("a single-column", "a composite index"),
       ("an index scan", "a table scan")],
    s=["a slow query despite an existing index", "writes slowing down after adding indexes"],
    d=["an indexing strategy for a read-heavy reporting table"])
add("Transactions & ACID",
    c=["ACID properties", "isolation levels", "locking", "MVCC", "deadlocks", "optimistic locking"],
    p=[("`READ COMMITTED`", "`SERIALIZABLE`"), ("optimistic", "pessimistic locking"),
       ("a dirty read", "a phantom read")],
    s=["a deadlock under concurrent updates", "lost updates from a race condition"],
    d=["a concurrency-safe inventory decrement at high traffic"])
add("Database Design & Normalization",
    c=["1NF/2NF/3NF", "primary and foreign keys", "denormalization", "surrogate vs natural keys",
       "many-to-many relationships", "constraints"],
    p=[("normalization", "denormalization"), ("a surrogate", "a natural key"),
       ("3NF", "star schema")],
    s=["update anomalies from a denormalized table", "a many-to-many modeled incorrectly"],
    d=["a schema for a multi-tenant SaaS app"])
add("Window Functions",
    c=["`ROW_NUMBER`", "`RANK`/`DENSE_RANK`", "`PARTITION BY`", "running totals", "`LAG`/`LEAD`",
       "moving averages"],
    p=[("`RANK`", "`DENSE_RANK`"), ("`ROW_NUMBER`", "`RANK`"), ("a window function", "`GROUP BY`")],
    prob=["rank employees by salary within each department", "compute a 7-day moving average",
          "find the running total of sales by date"])
add("Stored Procedures & Functions",
    c=["stored procedures", "user-defined functions", "triggers", "cursors", "control flow in SQL",
       "error handling in procedures"],
    p=[("a stored procedure", "a function"), ("a trigger", "application logic"),
       ("a cursor", "a set-based query")],
    s=["a trigger causing hidden performance problems", "a cursor making a job crawl"],
    d=["when to push logic into the database vs the app"])
add("NoSQL vs SQL",
    c=["document stores", "key-value stores", "wide-column stores", "denormalization in NoSQL",
       "eventual consistency", "access-pattern-first modeling"],
    p=[("SQL", "NoSQL"), ("a document", "a relational model"), ("strong", "eventual consistency")],
    s=["a NoSQL schema that can't support a new query", "joins faked in the app layer"],
    d=["choosing a datastore for a high-write event log"])

# ---------------- SYSTEM DESIGN (dedicated) ----------------
add("Scalability & Load Balancing",
    c=["horizontal scaling", "load balancers (L4/L7)", "statelessness", "sticky sessions",
       "health checks", "autoscaling", "connection draining"],
    p=[("horizontal", "vertical scaling"), ("L4", "L7 load balancing"),
       ("round-robin", "least-connections")],
    s=["one server hot while others idle", "sessions breaking after scaling out"],
    d=["a stateless, autoscaling web tier behind a load balancer"])
add("Caching Strategies",
    c=["cache-aside", "write-through", "write-behind", "TTL and eviction", "cache invalidation",
       "CDN caching", "the thundering-herd problem"],
    p=[("cache-aside", "write-through"), ("an LRU", "an LFU policy"),
       ("a local", "a distributed cache")],
    s=["cache stampede after a deploy", "stale data served from cache"],
    d=["a caching layer for a read-heavy product catalog"])
add("Database Design & Sharding",
    c=["sharding keys", "consistent hashing", "replication", "resharding", "cross-shard queries",
       "hot-shard mitigation"],
    p=[("sharding", "replication"), ("range", "hash sharding"), ("a leader", "a follower replica")],
    s=["a hot shard from a skewed key", "a cross-shard join killing performance"],
    d=["a sharded database that can rebalance without downtime"])
add("Consistency & CAP Theorem",
    c=["the CAP theorem", "strong vs eventual consistency", "quorums", "the PACELC extension",
       "read-your-writes consistency", "conflict resolution"],
    p=[("consistency", "availability"), ("strong", "eventual consistency"),
       ("a quorum read", "a single-node read")],
    s=["stale reads confusing users after a write", "split-brain during a network partition"],
    d=["a globally replicated store with tunable consistency"])
add("Message Queues & Streaming",
    c=["queues vs pub/sub", "at-least-once delivery", "dead-letter queues", "backpressure",
       "ordering guarantees", "consumer scaling"],
    p=[("a queue", "a stream"), ("at-least-once", "exactly-once"), ("push", "pull consumers")],
    s=["a growing backlog the consumers can't drain", "poison messages blocking a queue"],
    d=["a durable async pipeline that survives consumer outages"])
add("API & Microservices Design",
    c=["REST resource modeling", "pagination", "versioning", "idempotency", "rate limiting",
       "backward compatibility"],
    p=[("REST", "gRPC"), ("offset", "cursor pagination"), ("URI", "header versioning")],
    s=["a breaking API change that broke clients", "duplicate charges from retried POSTs"],
    d=["a versioned, idempotent public API"])
add("Real-World System Design",
    c=["requirement gathering", "capacity estimation", "the data model", "API design",
       "bottleneck analysis", "tradeoff discussion"],
    p=[("read-heavy", "write-heavy design"), ("SQL", "NoSQL for this case")],
    d=["a ride-sharing backend", "a video-streaming platform", "a distributed job scheduler",
       "an e-commerce checkout system", "a real-time analytics dashboard", "a social media feed"])
add("System Design Fundamentals",
    c=["latency vs throughput", "the back-of-envelope estimate", "the CDN", "the reverse proxy",
       "database indexing basics", "the read/write path"],
    p=[("latency", "throughput"), ("a proxy", "a load balancer"), ("stateless", "stateful services")],
    s=["a design that works at 100 users but not 1M", "a single point of failure in the diagram"],
    d=["a simple, scalable web architecture from scratch"])

# ---------------- DSA (dedicated) ----------------
add("Arrays & Strings",
    c=["in-place modification", "prefix sums", "the two-pointer pattern", "string hashing"],
    p=[("an array", "a linked list"), ("`O(n)`", "`O(n^2)` scanning")],
    prob=["Two Sum", "maximum subarray (Kadane's)", "product of array except self",
          "rotate an array in place", "longest common prefix", "valid anagram",
          "move zeroes to the end", "find the missing number"])
add("Linked Lists",
    c=["singly vs doubly linked lists", "the fast/slow pointer trick", "dummy-head nodes",
       "in-place reversal"],
    p=[("a singly", "a doubly linked list"), ("an array", "a linked list")],
    prob=["reverse a linked list", "detect a cycle", "find the middle node",
          "merge two sorted lists", "remove the nth node from the end",
          "check if a list is a palindrome"])
add("Stacks & Queues",
    c=["stack vs queue semantics", "monotonic stacks", "using two stacks for a queue",
       "expression evaluation"],
    p=[("a stack", "a queue"), ("an `ArrayDeque`", "a `LinkedList`")],
    prob=["valid parentheses", "min stack with O(1) getMin", "implement a queue with two stacks",
          "next greater element", "evaluate reverse Polish notation",
          "daily temperatures"])
add("Trees & BST",
    c=["tree traversals", "BST properties", "balanced trees", "tree height and depth",
       "the lowest common ancestor"],
    p=[("BFS", "DFS traversal"), ("a BST", "a heap"), ("in-order", "level-order traversal")],
    prob=["invert a binary tree", "validate a BST", "level-order traversal",
          "lowest common ancestor", "maximum depth of a tree", "serialize and deserialize a tree"])
add("Graphs (BFS/DFS)",
    c=["adjacency list vs matrix", "BFS shortest path", "topological sort", "cycle detection",
       "connected components", "Dijkstra's algorithm"],
    p=[("BFS", "DFS"), ("an adjacency list", "an adjacency matrix"),
       ("Dijkstra", "BFS for shortest path")],
    prob=["number of islands", "clone a graph", "course schedule (topological sort)",
          "shortest path in a grid", "detect a cycle in a directed graph"])
add("Dynamic Programming",
    c=["memoization vs tabulation", "optimal substructure", "overlapping subproblems",
       "state definition", "the knapsack pattern"],
    p=[("top-down memoization", "bottom-up tabulation"), ("greedy", "DP")],
    prob=["climbing stairs", "coin change", "longest increasing subsequence",
          "edit distance", "0/1 knapsack", "house robber", "longest common subsequence"])
add("Recursion & Backtracking",
    c=["the recursion call stack", "base cases", "the backtracking template", "pruning",
       "state restoration"],
    p=[("recursion", "iteration"), ("DFS", "backtracking")],
    prob=["generate all subsets", "permutations of an array", "N-Queens",
          "combination sum", "word search in a grid", "generate valid parentheses"])
add("Sorting & Searching",
    c=["quicksort vs mergesort", "stability", "binary search", "search on the answer space",
       "counting sort"],
    p=[("quicksort", "mergesort"), ("binary", "linear search"), ("a stable", "an unstable sort")],
    prob=["binary search", "search in a rotated sorted array", "find the kth largest element",
          "merge intervals", "first bad version", "find peak element"])
add("Two Pointers & Sliding Window",
    c=["the two-pointer technique", "the sliding-window pattern", "shrinking windows",
       "fast/slow pointers"],
    p=[("a fixed", "a variable-size window"), ("two pointers", "a hash map approach")],
    prob=["longest substring without repeating characters", "container with most water",
          "three-sum", "minimum window substring", "trapping rain water",
          "remove duplicates from a sorted array"])

# ── Generation ──
def dedupe_keep_order(items):
    seen, out = set(), []
    for it in items:
        k = it.strip().lower()
        if k not in seen:
            seen.add(k); out.append(it)
    return out

def gen_level(topic, level):
    data = D[topic]
    c, p, s, d, prob = data["c"], data["p"], data["s"], data["d"], data["prob"]
    q = []
    if level == JUNIOR:
        for x in c:
            q.append(random.choice(T_JUNIOR).format(c=x))
        for a, b in p:
            q.append(random.choice(T_JUNIOR_PAIR).format(a=a, b=b))
        for pr in prob:
            q.append(f"Explain the idea behind solving '{pr}' — what approach would you take?")
    elif level == MID:
        for x in c:
            q.append(random.choice(T_MID).format(c=x))
        for a, b in p:
            q.append(random.choice(T_MID_PAIR).format(a=a, b=b))
        for sc in s:
            q.append(random.choice(T_MID_SCEN).format(s=sc))
        for pr in prob:
            q.append(random.choice(T_PROB).format(p=pr))
    else:  # SENIOR
        for x in c:
            q.append(random.choice(T_SENIOR).format(c=x))
        for a, b in p:
            q.append(random.choice(T_SENIOR_PAIR).format(a=a, b=b))
        for sc in s:
            q.append(random.choice(T_SENIOR_SCEN).format(s=sc))
        for dd in d:
            q.append(random.choice(T_SENIOR_DESIGN).format(d=dd))
        for pr in prob:
            q.append(f"Optimize and extend '{pr}' for very large inputs — discuss tradeoffs.")

    q = dedupe_keep_order(q)
    random.shuffle(q)
    # Top up to PER_LEVEL with concept-based variety if short
    fillers_pool = c + [f"{a} vs {b}" for a, b in p]
    fi = 0
    while len(q) < PER_LEVEL and fillers_pool:
        base = fillers_pool[fi % len(fillers_pool)]; fi += 1
        extra = {
            JUNIOR: f"Describe a situation where {base} matters, and why.",
            MID: f"What tradeoffs come up when working with {base} in a real project?",
            SENIOR: f"How would {base} influence an architecture decision at scale?",
        }[level]
        if extra.strip().lower() not in {x.strip().lower() for x in q}:
            q.append(extra)
        if fi > len(fillers_pool) * 3:
            break
    q = q[:PER_LEVEL]
    return [f"{i+1}. {text}" for i, text in enumerate(q)]

bank = {}
total = 0
for topic in D:
    bank[topic] = {}
    for level in (JUNIOR, MID, SENIOR):
        qs = gen_level(topic, level)
        bank[topic][level] = qs
        total += len(qs)

with open("question_bank.json", "w", encoding="utf-8") as f:
    json.dump(bank, f, ensure_ascii=False, indent=2)

print(f"Topics: {len(bank)}")
print(f"Total questions: {total}")
counts = [len(bank[t][l]) for t in bank for l in bank[t]]
print(f"Per-level min/avg/max: {min(counts)}/{sum(counts)/len(counts):.1f}/{max(counts)}")
