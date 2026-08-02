from aiogram import Router

from handlers.feedback import router as feedback_router
from handlers.report import router as report_router
from handlers.start import router as start_router

router = Router()
router.include_router(feedback_router)
router.include_router(report_router)
router.include_router(start_router)