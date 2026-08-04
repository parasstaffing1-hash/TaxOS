"""Background Reporting Engine."""

import asyncio
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import openpyxl

# In-memory job store for background reports
_JOBS: dict[str, dict[str, Any]] = {}


class ReportingEngine:
    """Handles generating heavy Excel/PDF reports asynchronously in the background."""

    @staticmethod
    def get_job_status(job_id: str) -> dict[str, Any] | None:
        return _JOBS.get(job_id)

    @staticmethod
    async def generate_excel_report(job_id: str, report_name: str, data: dict[str, Any]) -> None:
        """Background task to generate an Excel report from analytics data."""
        try:
            # Simulate heavy processing if data is huge
            await asyncio.sleep(1)

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Analytics Report"

            # Write headers
            ws.append(
                ["Category", "Gross Income", "Total Tax", "Net Income", "Effective Rate (%)"]
            )

            # Write data rows (handles the Dict[str, CalculationResponse] structure generically)
            for key, calc_res in data.items():
                calc_dict = calc_res.model_dump() if hasattr(calc_res, "model_dump") else calc_res

                gross = float(calc_dict["gross_income"]["annual"])
                tax = float(calc_dict["total_tax"])
                net = float(calc_dict["net_income"]["annual"])
                rate = float(calc_dict["effective_tax_rate"])

                ws.append([str(key), gross, tax, net, rate])

            # Save to temp file
            tmp_dir = Path(tempfile.gettempdir()) / "taxos_reports"
            tmp_dir.mkdir(exist_ok=True)

            file_path = tmp_dir / f"{report_name}_{job_id}.xlsx"
            wb.save(file_path)

            _JOBS[job_id]["status"] = "completed"
            _JOBS[job_id]["file_path"] = str(file_path)

        except Exception as e:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = str(e)

    @classmethod
    def start_report_generation(
        cls, background_tasks: Any, report_name: str, data: dict[str, Any]
    ) -> str:
        """Enqueue the job and return a Job ID."""
        job_id = str(uuid4())
        _JOBS[job_id] = {"status": "processing", "file_path": None, "error": None}

        # Enqueue to FastAPI BackgroundTasks
        background_tasks.add_task(cls.generate_excel_report, job_id, report_name, data)
        return job_id
