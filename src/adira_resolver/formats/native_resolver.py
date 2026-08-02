from pathlib import Path
import logging
import shutil
import tempfile
from py7zz import SevenZipFile

logger = logging.getLogger(__name__)

class NativeResolverFromFile:
    """
    File semantics:
        server.fetch(output_dir) -> output_file (Path)
    resolver responsibilities:
        1. output_dir を作る
        2. server.fetch(output_dir) を呼ぶ
        3. 返ってきた blob を native transform に従って最終配置する
    """

    def __init__(self, dep_id, identity, fmt_params, retrieval_dir):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.retrieval_dir = Path(retrieval_dir)

    def retrieve(self, server, dry_run=False):
        """
        pre_fetch_process + fetch + post_fetch_process を統合したメソッド。

        1. blob を受け取るための tempdir を作る
        2. server.fetch(tempdir) を呼ぶ（File semantics: blob_path が返る）
        3. blob_path を native transform に従って最終配置する
        """
        dst_root = self.fmt_params.get("dst_root", "native")
        dst_rel = self.fmt_params.get("dst", self.dep_id)
        final_dir = self.retrieval_dir / dst_root / dst_rel

        if not dry_run:
            # 1. blob を受け取るための tempdir
            with tempfile.TemporaryDirectory(prefix=f"adira_native_{self.dep_id}_") as tempdir_str:
                tempdir = Path(tempdir_str)
                self._place(tempdir, server, final_dir)
        else:
            self._place(None, server, final_dir)

        return None

    # -------------------------
    # 最終配置処理（旧 post_fetch_process）
    # -------------------------
    def _place(self, tempdir: Path, server, final_dir: Path):
        if final_dir.exists() and any(final_dir.iterdir()):
            logger.info("native transform: final_dir %s already exists and is not empty; skipping", final_dir)
            return

        dry_run = tempdir is None

        # 2. server.fetch(tempdir) → blob_path
        blob_path = server.fetch(self.identity, tempdir, dry_run)

        # 3. native transform に従って最終配置

        transform = self.fmt_params.get("transform")

        if transform is None:
            # 変換なし → blob をそのまま配置
            if dry_run:
                logger.info("[dry-run] placing %s into %s", self.identity, final_dir)
            else:
                target = final_dir / blob_path.name
                self._safe_move(blob_path, target)
            return

        if dry_run:
            logger.info("[dry-run] extracting %s into %s (transform=%s)", self.identity, final_dir, transform)
        else:
            # 展開先の第二の tempdir（with で安全に）
            with tempfile.TemporaryDirectory(prefix=f"adira_native_extract_{self.dep_id}_") as extract_temp_str:
                extract_temp = Path(extract_temp_str)

                # py7zz 汎用展開
                self._extract_generic(blob_path, extract_temp)

                strip_root = self._get_strip_root_params(transform)

                if strip_root:
                    # 一階層目（ルートディレクトリ配下）を final_dir に移動
                    root = self._detect_single_root_dir(extract_temp)
                    for item in root.iterdir():
                        target = final_dir / item.name
                        self._safe_move(item, target)
                else:
                    # 二階層目（extract_temp 直下）を final_dir に移動
                    for item in extract_temp.iterdir():
                        target = final_dir / item.name
                        self._safe_move(item, target)

    # -------------------------
    # 汎用アーカイブ → py7zz
    # -------------------------
    def _extract_generic(self, blob_path: Path, extract_temp: Path):
        """
        zip / 7z / tar 系など「py7zz が対応しているフォーマット」は
        すべて SevenZipFile 経由で展開する。
        """
        with SevenZipFile(blob_path, mode="r") as archive:
            archive.extractall(path=extract_temp)

    # -------------------------
    # 共通ユーティリティ
    # -------------------------
    def _safe_move(self, src: Path, dst: Path):
        if dst.exists():
            raise RuntimeError(f"native transform: '{dst}' already exists")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    def _detect_single_root_dir(self, base: Path) -> Path:
        entries = [e for e in base.iterdir() if e.is_dir()]
        if len(entries) != 1:
            raise RuntimeError("native transform strip_root: 直下に 1 つのルートディレクトリが存在しません")
        return entries[0]

    def _get_strip_root_params(self, transform: str) -> bool:
        params = self.fmt_params.get(transform, {})
        return params.get("strip_root", False)
