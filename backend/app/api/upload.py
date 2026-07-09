"""
文件上传 API 路由
支持向知识库上传多种格式的文档文件
"""

import os
import shutil
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from app.config import settings
from app.core.rag_engine import rag_engine

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 支持的文件扩展名
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".csv"}


@router.post("/{kb_id}")
async def upload_files(
    kb_id: str,
    files: List[UploadFile] = File(...),
):
    """
    上传文件到指定知识库

    - 接受多个文件上传
    - 保存到 config.UPLOAD_DIR/{kb_id}/
    - 调用 rag_engine 进行文档入库
    - 返回上传结果和分块统计
    """
    if not files:
        raise HTTPException(status_code=400, detail="未提供任何文件")

    # 确保上传目录存在
    upload_dir = os.path.join(settings.UPLOAD_DIR, kb_id)
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    file_results = []
    total_chunks = 0

    for upload_file in files:
        # 检查文件扩展名
        filename = upload_file.filename or "unknown"
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            file_results.append({
                "filename": filename,
                "size": 0,
                "chunks": 0,
                "error": f"不支持的文件类型: {ext}，支持的格式: {', '.join(ALLOWED_EXTENSIONS)}",
            })
            continue

        try:
            # 保存上传文件
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)

            file_size = os.path.getsize(file_path)
            saved_paths.append(file_path)

            file_results.append({
                "filename": filename,
                "size": file_size,
                "chunks": 0,  # 稍后更新
            })

        except Exception as e:
            file_results.append({
                "filename": filename,
                "size": 0,
                "chunks": 0,
                "error": f"文件保存失败: {str(e)}",
            })

    # 对成功保存的文件进行文档入库
    if saved_paths:
        try:
            result = rag_engine.ingest_documents(kb_id, saved_paths)
            chunk_count = result.get("chunk_count", 0)
            total_chunks = chunk_count

            # 更新每个文件的分块数（均匀分配）
            saved_count = len(saved_paths)
            if saved_count > 0 and chunk_count > 0:
                avg_chunks = chunk_count // saved_count
                remainder = chunk_count % saved_count
                idx = 0
                for fr in file_results:
                    if "error" not in fr and fr["size"] > 0:
                        fr["chunks"] = avg_chunks + (1 if idx < remainder else 0)
                        idx += 1

        except Exception as e:
            # 文档入库失败，但不影响文件保存
            for fr in file_results:
                if "error" not in fr:
                    fr["error"] = f"文档入库失败: {str(e)}"

    return {
        "kb_id": kb_id,
        "files": file_results,
        "total_chunks": total_chunks,
    }
