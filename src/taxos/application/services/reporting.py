"""Background Reporting Engine."""

import asyncio
import io
from typing import Any
from uuid import uuid4

import openpyxl

from taxos.infrastructure.storage.object_storage import get_object_storage

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

            output = io.BytesIO()
            wb.save(output)
            payload = output.getvalue()
            storage_key = f"reports/{job_id}/{report_name}.xlsx"
            stored = await get_object_storage().put_bytes(
                storage_key,
                payload,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                content_disposition=f'attachment; filename="{report_name}_{job_id}.xlsx"',
                metadata={"job-id": job_id},
            )

            _JOBS[job_id]["status"] = "completed"
            _JOBS[job_id]["storage_key"] = stored.key
            _JOBS[job_id]["storage_backend"] = stored.backend

        except Exception as e:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = str(e)

    @classmethod
    def start_report_generation(
        cls, background_tasks: Any, report_name: str, data: dict[str, Any]
    ) -> str:
        """Enqueue the job and return a Job ID."""
        job_id = str(uuid4())
        _JOBS[job_id] = {
            "status": "processing",
            "storage_key": None,
            "storage_backend": None,
            "error": None,
        }

        # Enqueue to FastAPI BackgroundTasks
        background_tasks.add_task(cls.generate_excel_report, job_id, report_name, data)
        return job_id
