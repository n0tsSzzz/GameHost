from prometheus_client import Counter, Gauge, Histogram

SERVER_TOTAL = Gauge("gh_servers_total", "Servers by status", ["status"])
TASK_DURATION = Histogram("gh_task_duration_seconds", "Task duration by kind", ["kind"])
NODE_CAPACITY_USED = Gauge("gh_node_capacity_used_ratio", "Node capacity used ratio", ["node"])
ARQ_JOBS_IN_FLIGHT = Gauge("gh_arq_jobs_in_flight", "ARQ jobs in flight")
ARQ_JOBS_FAILED = Counter("gh_arq_jobs_failed_total", "Failed ARQ jobs")
