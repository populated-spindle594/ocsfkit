def normalize_login_status(value):
    return "Success" if str(value).lower() == "success" else "Failure"


def login_status_to_id(value):
    return 1 if str(value).lower() == "success" else 2


def azure_status_text(value):
    return "Success" if int(value) == 0 else "Failure"


def azure_status_id(value):
    return 1 if int(value) == 0 else 2


TRANSFORMS = {
    "normalize_login_status": normalize_login_status,
    "login_status_to_id": login_status_to_id,
    "azure_status_text": azure_status_text,
    "azure_status_id": azure_status_id,
}
