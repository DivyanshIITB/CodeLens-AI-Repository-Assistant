import os
import zipfile
import shutil
import httpx
from pathlib import Path
from backend.config.settings import settings
from backend.config.logger import logger

class RepoCloner:
    @staticmethod
    def clone_or_download(repo_url: str, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            import git
            logger.info(f"Cloning repository via GitPython from {repo_url} to {target_dir}")
            git.Repo.clone_from(repo_url, target_dir, depth=1)
            return target_dir
        except Exception as git_err:
            logger.warning(f"GitPython clone failed ({git_err}). Trying GitHub ZIP download fallback...")

        if "github.com" in repo_url:
            clean_url = repo_url.rstrip("/").removesuffix(".git")
            zip_url = f"{clean_url}/archive/refs/heads/main.zip"
            zip_path = target_dir.parent / f"{target_dir.name}.zip"

            try:
                with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                    resp = client.get(zip_url)
                    if resp.status_code != 200:
                        zip_url = f"{clean_url}/archive/refs/heads/master.zip"
                        resp = client.get(zip_url)

                    if resp.status_code == 200:
                        zip_path.write_bytes(resp.content)
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            temp_extract = target_dir.parent / f"{target_dir.name}_temp"
                            zip_ref.extractall(temp_extract)
                            
                            extracted_subdirs = list(temp_extract.glob("*"))
                            if extracted_subdirs and extracted_subdirs[0].is_dir():
                                for item in extracted_subdirs[0].iterdir():
                                    shutil.move(str(item), str(target_dir))
                            shutil.rmtree(temp_extract, ignore_errors=True)

                        if zip_path.exists():
                            os.remove(zip_path)

                        logger.info(f"Successfully downloaded and extracted GitHub archive to {target_dir}")
                        return target_dir
            except Exception as zip_err:
                logger.error(f"ZIP download fallback failed: {zip_err}")

        raise RuntimeError(f"Failed to clone or download repository from {repo_url}")

    @staticmethod
    def extract_zip(zip_bytes: bytes, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        temp_zip = target_dir.parent / f"upload_{target_dir.name}.zip"
        temp_zip.write_bytes(zip_bytes)

        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        if temp_zip.exists():
            os.remove(temp_zip)

        subdirs = [p for p in target_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        files = [p for p in target_dir.iterdir() if p.is_file()]
        if len(subdirs) == 1 and not files:
            single_dir = subdirs[0]
            temp_move = target_dir.parent / f"flatten_{target_dir.name}"
            shutil.move(str(single_dir), str(temp_move))
            shutil.rmtree(target_dir, ignore_errors=True)
            shutil.move(str(temp_move), str(target_dir))

        logger.info(f"Successfully extracted uploaded ZIP file to {target_dir}")
        return target_dir
