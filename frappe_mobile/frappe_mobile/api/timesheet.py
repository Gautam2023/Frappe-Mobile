import frappe
import json
from frappe import _

@frappe.whitelist()
def create_timesheet(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        employee = data.get("employee")
        parent_project = data.get("parent_project")
        time_logs = data.get("time_logs")

        if not employee:
            frappe.throw(_("Employee is required"))

        if not time_logs or not isinstance(time_logs, list):
            frappe.throw(_("At least one time log is required"))

        current_employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if employee != current_employee:
            frappe.throw(_("You can only create a timesheet for yourself"))

        timesheet_data = {
            "doctype": "Timesheet",
            "employee": employee,
            "time_logs": []
        }

        if parent_project:
            timesheet_data["parent_project"] = parent_project

        for idx, row in enumerate(time_logs, start=1):
            if not row.get("from_time") or not row.get("to_time"):
                frappe.throw(_(f"Row {idx}: From Time and To Time are required"))

            if not row.get("task"):
                frappe.throw(_(f"Row {idx}: Task is required in time logs"))
            
            if not row.get("description"):
                frappe.throw(_(f"Row {idx}: Description is required in time logs"))
            
            timesheet_data["time_logs"].append({
                "activity_type": row.get("activity_type"),
                "from_time": row.get("from_time"),
                "to_time": row.get("to_time"),
                "project": row.get("project"),
                "task": row.get("task"),
                "description": row.get("description"),
                "is_billable": row.get("is_billable", 0)
            })

        timesheet = frappe.get_doc(timesheet_data)
        try:
            timesheet.insert()
        except frappe.PermissionError:
            frappe.throw(_("You do not have permission to create a Timesheet"))

        return {
            "status": "success",
            "timesheet": timesheet.name
        } 
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Mobile Timesheet API Error")
        frappe.throw(_("Failed to create timesheet"))


@frappe.whitelist()
def list_timesheets(data=None):
    try:
        if data and isinstance(data, str):
            data = json.loads(data)
        else:
            data = data or {}

        from_date = data.get("from_date")
        to_date = data.get("to_date")
        limit = int(data.get("limit", 20))
        offset = int(data.get("offset", 0))

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            "name"
        )

        if not employee:
            frappe.throw(_("Employee not linked to user"))

        filters = {
            "employee": employee
        }

        if from_date and to_date:
            filters["start_date"] = ["between", [from_date, to_date]]

        timesheets = frappe.get_all(
            "Timesheet",
            filters = filters,
            fields=[
                "name",
                "parent_project",
                "status",
                "total_hours",
                "start_date"
            ],
            order_by="start_date desc",
            limit_start=offset,
            limit_page_length=limit
        )

        return {
            "status": "success",
            "data": timesheets
        }
    
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Mobile List Timesheets API Error"
        )
        frappe.throw(_("Failed to fetch timesheets"))

@frappe.whitelist()
def get_projects():
    return frappe.get_all(
        "Project",
        fields=["name"],
        order_by="name"
    )