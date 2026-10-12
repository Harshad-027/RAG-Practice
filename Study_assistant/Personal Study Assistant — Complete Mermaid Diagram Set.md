# Personal Study Assistant — Complete Mermaid Diagram Set

> **Legend:** Required MVP features are shown as solid paths. Optional and future items are explicitly labelled. The application remains one modular FastAPI backend rather than separate microservices.

## 1. End-to-end architecture and data flow

```mermaid
flowchart LR
    student@{ shape: person, label: "Student" }

    subgraph client ["Web client — Required MVP"]
        ui@{ shape: browser, label: "Study workspace\nDocuments · Markdown notes · chat · quizzes" }
        inspect["Evidence inspector\nexcerpt · heading · page/section"]
        ui --> inspect
    end

    subgraph api ["Single FastAPI backend — modular Required MVP"]
        auth["Authentication + authorization\nresolve authenticated user"]
        scope{"Authorized resource?"}
        docs["Document API\nupload · list · update · delete"]
        notes["Markdown Notes API\ncreate · edit · save · list · delete"]
        classify{"Request classifier\nquestion · summary · quiz"}
        answer["Answer service\ngrounded response + citations"]
        summary["Summarization service\ngrounded summary + citations"]
        quiz["Quiz service\ngenerate · grade · evidence-based explanation"]
        topic["Topic assignment\nmetadata, validated label, or Unclassified"]
        progress["Quiz attempts + progress\nno weak-topic claim with insufficient data"]
        lifecycle["Lifecycle coordinator\nversioning · invalidation · safe cleanup retry"]
        monitor["Operational monitoring\nlatency · tokens · estimated cost"]
    end

    subgraph ingest ["Document processing — Required MVP"]
        extract["Extract file or Markdown\npreserve title, headings, hierarchy, pages/sections"]
        chunk["Create versioned chunks\nowner ID · chunk index · source references"]
        embed["Embed chunks"]
    end

    subgraph retrieve ["Retrieval"]
        semantic["Semantic vector search — Required MVP\nowner + active-version filter"]
        keyword["Keyword search — Optional\nowner + active-version filter"]
        merge["Merge results — Optional"]
        rerank["Rerank results — Optional"]
        evidence["Evidence set\nexcerpts + metadata for citations"]
    end

    subgraph data ["Private data stores — Required MVP"]
        files@{ shape: folder, label: "Original file storage\nlocal private disk (dev) or object storage (prod)" }
        pg@{ shape: cyl, label: "PostgreSQL\nownership · metadata · notes · chunks · conversations\ncitations · quiz attempts · progress · cleanup status" }
        vectors@{ shape: cyl, label: "Vector index\nembeddings + user/document/version IDs" }
    end

    student --> ui
    ui -->|authenticated request| auth --> scope
    scope -->|allowed| docs & notes & classify
    scope -->|denied| ui

    docs --> files & pg
    notes --> pg
    docs --> extract
    notes --> extract
    extract --> chunk --> embed --> vectors
    chunk --> pg

    classify --> semantic
    semantic -. Optional .-> keyword
    semantic -. Optional .-> merge
    keyword -.-> merge
    merge -. Optional .-> rerank
    semantic --> evidence
    merge -.-> evidence
    rerank -.-> evidence

    evidence --> answer & summary & quiz
    quiz --> topic --> pg
    quiz --> progress --> pg
    answer & summary & quiz --> ui
    evidence --> inspect

    docs -->|update or delete| lifecycle
    lifecycle --> files & pg & vectors
    auth --> monitor
    semantic --> monitor
    answer & summary & quiz --> monitor

    classDef required fill:#eef2ff,stroke:#818cf8,color:#1e1b4b
    classDef security fill:#fef2f2,stroke:#f87171,color:#450a0a
    classDef data fill:#f0fdfa,stroke:#2dd4bf,color:#042f2e
    classDef optional fill:#fff7ed,stroke:#fb923c,color:#431407
    class ui,inspect,docs,notes,classify,answer,summary,quiz,topic,progress,lifecycle,extract,chunk,embed,semantic,evidence,monitor required
    class auth,scope security
    class files,pg,vectors data
    class keyword,merge,rerank optional
```

## 2. Backend component design

```mermaid
flowchart TB
    web@{ shape: browser, label: "Study workspace" }

    subgraph backend ["Single FastAPI backend — Required MVP"]
        auth["Auth and authorization\nresolve user and resource scope"]
        documentApi["Document module\nupload · list · update · delete"]
        noteApi["Markdown Notes module\ncreate · edit · save · list · delete"]
        conversation["Conversation module\nmessages and citations"]
        classifier{"Request classifier"}
        answer["Question-answering service"]
        summary["Summarization service"]
        quiz["Quiz service\ngenerate · grade · explain from evidence"]
        topic["Topic module\nmetadata, validated label, or Unclassified"]
        progress["Progress module\nrecord attempts and assessment sufficiency"]
        lifecycle["Lifecycle coordinator\nversioning and cleanup recovery"]
        retrieval["Retrieval module\nsemantic MVP; hybrid/reranking optional"]
    end

    web --> auth
    auth --> documentApi & noteApi & conversation & classifier
    classifier -->|question| answer
    classifier -->|summary| summary
    classifier -->|quiz request| quiz
    answer & summary & quiz --> retrieval
    quiz --> topic --> progress
    documentApi --> lifecycle

    classDef core fill:#eef2ff,stroke:#818cf8,color:#1e1b4b
    classDef security fill:#fef2f2,stroke:#f87171,color:#450a0a
    classDef decision fill:#fefce8,stroke:#facc15,color:#422006
    class auth security
    class classifier decision
    class web,documentApi,noteApi,conversation,answer,summary,quiz,topic,progress,lifecycle,retrieval core
```

## 3. RAG request sequence and evidence inspection

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Web as Study workspace
    participant API as FastAPI backend
    participant Auth as Auth and authorization
    participant RAG as Retrieval module
    participant PG as PostgreSQL
    participant Vec as Vector index
    participant LLM as LLM provider

    Student->>Web: Ask question, request summary, or generate quiz
    Web->>API: Authenticated request
    API->>Auth: Resolve user and authorize resource IDs
    Auth->>PG: Check ownership and active document version
    PG-->>Auth: Authorized resources only
    API->>API: Classify request type
    API->>RAG: Retrieve with user ID and active-version filter
    RAG->>Vec: Semantic search scoped to authorized resources
    Vec-->>RAG: Candidate chunk IDs
    opt Optional hybrid retrieval
        RAG->>PG: Keyword search scoped to authorized resources
        PG-->>RAG: Keyword candidates
        RAG->>RAG: Merge and optionally rerank candidates
    end
    RAG->>PG: Load excerpts, title, heading, and page/section locator
    PG-->>RAG: Evidence set and citation metadata
    RAG->>LLM: Task prompt with retrieved evidence
    LLM-->>RAG: Grounded answer, summary, or quiz draft
    RAG-->>API: Result with citations
    API-->>Web: Response and evidence references
    Student->>Web: Inspect citation
    Web->>API: Request authorized source excerpt
    API-->>Web: Excerpt, title, heading, and locator
```

## 4. Domain and database class model

```mermaid
classDiagram
    direction LR

    class User {
        +UUID id
        +String email
        +DateTime createdAt
    }
    class Document {
        +UUID id
        +UUID ownerId
        +String title
        +String storageKey
        +String status
        +DateTime updatedAt
    }
    class DocumentVersion {
        +UUID id
        +int versionNumber
        +String processingStatus
        +String cleanupStatus
    }
    class MarkdownNote {
        +UUID id
        +UUID ownerId
        +String title
        +Text markdownContent
        +DateTime updatedAt
    }
    class Chunk {
        +UUID id
        +int chunkIndex
        +String headingPath
        +String pageOrSectionRef
        +String contentHash
        +Boolean active
    }
    class VectorRecord {
        +UUID chunkId
        +UUID ownerId
        +UUID documentVersionId
        +String vectorStoreKey
    }
    class Conversation {
        +UUID id
        +UUID ownerId
        +DateTime createdAt
    }
    class Citation {
        +UUID id
        +String excerpt
        +String locator
    }
    class QuizQuestion {
        +UUID id
        +String prompt
        +String topicLabel
        +String topicStatus
    }
    class QuizAttempt {
        +UUID id
        +Boolean correct
        +DateTime attemptedAt
    }
    class ProgressRecord {
        +UUID id
        +String topicLabel
        +int evidenceCount
        +String confidenceStatus
    }

    User "1" --> "*" Document : owns
    User "1" --> "*" MarkdownNote : owns
    User "1" --> "*" Conversation : owns
    Document "1" *-- "*" DocumentVersion : versions
    DocumentVersion "1" *-- "*" Chunk : contains
    Chunk "1" --> "0..1" VectorRecord : indexed as
    Conversation "1" --> "*" Citation : returns
    Citation "*" --> "1" Chunk : supports
    User "1" --> "*" QuizAttempt : makes
    QuizQuestion "1" --> "*" QuizAttempt : answered by
    User "1" --> "*" ProgressRecord : has
```

## 5. Document ingestion, retrieval, update, and deletion data flow

```mermaid
flowchart LR
    source["Uploaded document or saved Markdown note"] --> extract["Extract content\npreserve title, headings, hierarchy, pages/sections"]
    extract --> version["Create document version"]
    version --> chunks["Create indexed chunks\nowner ID · heading path · locator · chunk index"]
    chunks --> pg@{ shape: cyl, label: "PostgreSQL metadata" }
    chunks --> embed["Create embeddings"]
    embed --> vectors@{ shape: cyl, label: "Vector index" }
    source --> originals@{ shape: folder, label: "Original file storage" }

    query["Authorized user request"] --> filter["Apply owner and active-version filter"]
    filter --> semantic["Semantic search — MVP"]
    filter -. Optional .-> keyword["Keyword search"]
    semantic --> evidence["Evidence set and citations"]
    keyword -. Optional merge .-> merge["Merge and optional rerank"]
    semantic -. Optional merge .-> merge
    merge -.-> evidence
    evidence --> response["Grounded answer, summary, or quiz explanation"]

    update["Update or delete document"] --> lifecycle["Mark old version stale\nqueue rebuild or cleanup"]
    lifecycle --> pg & vectors & originals
    lifecycle --> recovery["Retry incomplete cleanup safely\nretain audit status"]

    classDef required fill:#f0fdfa,stroke:#2dd4bf,color:#042f2e
    classDef optional fill:#fff7ed,stroke:#fb923c,color:#431407
    classDef storage fill:#eef2ff,stroke:#818cf8,color:#1e1b4b
    class source,extract,version,chunks,embed,query,filter,semantic,evidence,response,update,lifecycle,recovery required
    class keyword,merge optional
    class pg,vectors,originals storage
```

## 6. Security and user-isolation flow

```mermaid
flowchart TB
    request["Authenticated request\nverified session or token"] --> validate["Validate token and request"]
    validate --> action{"Requested action"}
    action -->|document or note| ownership["Check owner ID and authorization"]
    action -->|conversation or citation| conversationScope["Scope to user's conversation and cited chunks"]
    action -->|quiz or progress| assessmentScope["Scope attempts and progress to user"]

    ownership --> allowed{"Authorized resource?"}
    conversationScope --> allowed
    assessmentScope --> allowed
    allowed -->|No| deny["Return 403 or safe not-found response"]
    allowed -->|Yes| scope["Pass user ID, resource IDs, and active version\nto every query and retrieval call"]

    scope --> postgres["PostgreSQL query\nWHERE owner_id = authenticated user"]
    scope --> vector["Vector metadata filter\nowner ID and active version"]
    scope --> files["Private file access\nserver-mediated authorized download"]
    postgres & vector & files --> audit["Audit-safe operational events\nno raw study content by default"]

    classDef security fill:#fef2f2,stroke:#f87171,color:#450a0a
    classDef safe fill:#f0fdf4,stroke:#4ade80,color:#052e16
    classDef data fill:#ecfeff,stroke:#22d3ee,color:#083344
    class request,validate,ownership,conversationScope,assessmentScope,scope,audit security
    class allowed,deny safe
    class postgres,vector,files data
```

## 7. Evaluation and operational monitoring

```mermaid
flowchart TB
    subgraph mvp ["Required MVP instrumentation"]
        app["FastAPI modules"] --> metrics["Record latency, errors, token usage, estimated model cost"]
        rag["Retrieval and answer path"] --> quality["Capture retrieval IDs, citation presence, and outcome signals"]
        metrics --> logs["Operational logs and metrics"]
        quality --> logs
    end

    subgraph optional ["Optional evaluation and analytics"]
        dataset["Curated authorized evaluation set"] --> offline["Offline RAG evaluation\nretrieval quality · groundedness · citation accuracy"]
        logs -. sampled signals .-> review["Manual quality review"]
        events["Product events"] --> posthog["PostHog — Optional"]
    end

    subgraph future ["Future work"]
        dashboard["Advanced observability dashboards\nand automated regression gates"]
        advanced["Stronger topic and weak-topic analytics\nafter sufficient assessment evidence"]
    end

    offline --> dashboard
    review --> dashboard
    logs -. future .-> dashboard
    offline -. future .-> advanced

    classDef required fill:#eef2ff,stroke:#818cf8,color:#1e1b4b
    classDef optionalStyle fill:#fff7ed,stroke:#fb923c,color:#431407
    classDef futureStyle fill:#f5f3ff,stroke:#a78bfa,color:#2e1065
    class app,rag,metrics,quality,logs required
    class dataset,offline,review,events,posthog optionalStyle
    class dashboard,advanced futureStyle
```

## 8. Document lifecycle state model

```mermaid
stateDiagram-v2
    [*] --> Uploaded
    Uploaded --> Processing: create version
    Processing --> Active: chunks and vectors ready
    Processing --> ProcessingFailed: extraction or indexing failure
    ProcessingFailed --> Processing: retry

    Active --> Updating: content changed
    Updating --> Processing: create replacement version
    Active --> DeletionRequested: user deletes document
    DeletionRequested --> CleanupPending: mark inaccessible and stale
    CleanupPending --> Deleted: metadata, vectors, and file removed
    CleanupPending --> CleanupIncomplete: one or more cleanup steps fail
    CleanupIncomplete --> CleanupPending: safe retry
    Deleted --> [*]

    note right of Active
        Retrieval requires matching owner ID
        and an active document version.
    end note
```

## 9. Development and production deployment

```mermaid
architecture-beta
    group client(internet)[Client]
    service browser(internet)[Browser] in client

    group app(cloud)[Application runtime]
    service fastapi(server)[FastAPI application] in app
    service worker(server)[Worker or in-process jobs] in app

    group dev(cloud)[Development option]
    service localfiles(disk)[Private local files] in dev
    service localvector(database)[Local vector index] in dev

    group prod(cloud)[Production option]
    service objectstore(disk)[Private object storage] in prod
    service managedvector(database)[Managed vector database - Future] in prod

    service postgres(database)[PostgreSQL]
    service llm(internet)[LLM API]

    browser:R --> L:fastapi
    fastapi:R --> L:worker
    fastapi:B --> T:postgres
    fastapi:R --> L:llm
    worker:B --> T:localfiles
    worker:R --> L:localvector
    worker:B --> T:objectstore
    worker:R --> L:managedvector
```