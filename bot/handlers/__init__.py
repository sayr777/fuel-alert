from aiogram import Router

from handlers.report import router as report_router
from handlers.start import router as start_router

router = Router()
router.include_router(start_router)
router.include_router(report_router)