# data_pipeline
collect and process data

An overview of the workflow is shown in [workflow_diagram](workflow_diagram/).

The current status of the URLBuilder section is contained in [updated_urlbuilder](updated_urlbuilder), and the status of the site worker/miner section is contained in [pubsub_workers](pubsub_workers) or [rabbitmq_workers](rabbitmq_workers).

Note that rabbitmq workers are currently more stable regarding the queueing system (because it's simpler), but pubsub has additional work from Gulnoza, in implementing a factory method for choosing a worker.
