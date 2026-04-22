from bot.handlers.start import register_start_handlers
from bot.handlers.providers import register_provider_handlers
from bot.handlers.purchase import register_purchase_handlers
from bot.handlers.resources import register_resource_handlers
from bot.handlers.upload import register_upload_handlers
from bot.handlers.jobs import register_job_handlers
from bot.handlers.earnings import register_earnings_handlers
from bot.handlers.compare import register_compare_handlers
from bot.handlers.estimate import register_estimate_handlers


def register_all_handlers(app, db):
    """Register every handler group with the Application."""
    register_start_handlers(app, db)
    register_provider_handlers(app, db)
    register_purchase_handlers(app, db)
    register_resource_handlers(app, db)
    register_upload_handlers(app, db)
    register_job_handlers(app, db)
    register_earnings_handlers(app, db)
    register_compare_handlers(app, db)
    register_estimate_handlers(app, db)
