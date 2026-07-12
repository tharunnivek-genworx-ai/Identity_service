-- Drop Procrastinate schema objects (procrastinate 3.9.0)

DROP TRIGGER IF EXISTS procrastinate_trigger_delete_jobs_v1 ON procrastinate_jobs;
DROP TRIGGER IF EXISTS procrastinate_trigger_abort_requested_events_v1 ON procrastinate_jobs;
DROP TRIGGER IF EXISTS procrastinate_trigger_scheduled_events_v1 ON procrastinate_jobs;
DROP TRIGGER IF EXISTS procrastinate_trigger_status_events_insert_v1 ON procrastinate_jobs;
DROP TRIGGER IF EXISTS procrastinate_trigger_status_events_update_v1 ON procrastinate_jobs;
DROP TRIGGER IF EXISTS procrastinate_jobs_notify_queue_job_aborted_v1 ON procrastinate_jobs;
DROP TRIGGER IF EXISTS procrastinate_jobs_notify_queue_job_inserted_v1 ON procrastinate_jobs;

DROP TABLE IF EXISTS procrastinate_events CASCADE;
DROP TABLE IF EXISTS procrastinate_periodic_defers CASCADE;
DROP TABLE IF EXISTS procrastinate_jobs CASCADE;
DROP TABLE IF EXISTS procrastinate_workers CASCADE;

DROP FUNCTION IF EXISTS procrastinate_defer_jobs_v1(procrastinate_job_to_defer_v1[]) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_defer_periodic_job_v2(
    character varying,
    character varying,
    character varying,
    character varying,
    integer,
    character varying,
    bigint,
    jsonb
) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_fetch_job_v2(character varying[], bigint) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_finish_job_v1(bigint, procrastinate_job_status, boolean) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_cancel_job_v1(bigint, boolean, boolean) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_retry_job_v1(
    bigint,
    timestamp with time zone,
    integer,
    character varying,
    character varying
) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_retry_job_v2(
    bigint,
    timestamp with time zone,
    integer,
    character varying,
    character varying
) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_notify_queue_job_inserted_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_notify_queue_abort_job_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_trigger_function_status_events_insert_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_trigger_function_status_events_update_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_trigger_function_scheduled_events_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_trigger_abort_requested_events_procedure_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_unlink_periodic_defers_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_register_worker_v1() CASCADE;
DROP FUNCTION IF EXISTS procrastinate_unregister_worker_v1(bigint) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_update_heartbeat_v1(bigint) CASCADE;
DROP FUNCTION IF EXISTS procrastinate_prune_stalled_workers_v1(float) CASCADE;

DROP TYPE IF EXISTS procrastinate_job_to_defer_v1 CASCADE;
DROP TYPE IF EXISTS procrastinate_job_event_type CASCADE;
DROP TYPE IF EXISTS procrastinate_job_status CASCADE;
