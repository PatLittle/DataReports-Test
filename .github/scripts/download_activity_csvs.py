import io
import os
from pathlib import Path

import pandas as pd
from azure.storage.blob import ContainerClient

CSV_FILES_TO_PROCESS = [
    "ati_activity.csv", "ati_nil_activity.csv", "briefingt_activity.csv",
    "briefingt_nil_activity.csv", "consultations_activity.csv", "contracts_activity.csv",
    "contracts_nil_activity.csv", "contractsa_activity.csv", "dac_activity.csv",
    "grants_activity.csv", "grants_nil_activity.csv", "hospitalityq_activity.csv",
    "hospitalityq_nil_activity.csv", "qpnotes_activity.csv", "qpnotes_nil_activity.csv",
    "reclassification_activity.csv", "reclassification_nil_activity.csv", "travela_activity.csv",
    "travelq_activity.csv", "travelq_nil_activity.csv", "wrongdoing_activity.csv",
]


def title_case_from_filename(filename: str) -> str:
    stem = filename.replace("_activity.csv", "").replace(".csv", "")
    words = stem.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def main() -> None:
    container_url = os.environ["CONTAINER_URL"]
    sas_token = os.environ["SAS_TOKEN"]
    container_name = os.environ.get("CONTAINER_NAME")

    if container_name and container_name not in container_url:
        print(f"Warning: CONTAINER_NAME '{container_name}' was provided but does not appear in CONTAINER_URL")

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    pages_dir = Path("pages") / "data-tables"
    pages_dir.mkdir(parents=True, exist_ok=True)

    container_client = ContainerClient.from_container_url(container_url=container_url, credential=sas_token)

    for blob_name in CSV_FILES_TO_PROCESS:
        blob_client = container_client.get_blob_client(blob_name)
        print(f"Downloading {blob_name}...")
        data = blob_client.download_blob().readall()

        df = pd.read_csv(io.BytesIO(data))
        if "log_activity" in df.columns:
            df = df[df["log_activity"] == "D"]

        output_path = output_dir / blob_name
        df.to_csv(output_path, index=False)
        print(f"Saved {output_path} ({len(df)} rows)")

        table_title = title_case_from_filename(blob_name)
        page_path = pages_dir / f"{blob_name.replace('.csv', '.md')}"
        page_path.write_text(
            "\n".join(
                [
                    f"# {table_title}",
                    "",
                    "```yaml table",
                    f"data: data/{blob_name}",
                    "width: 1000",
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
