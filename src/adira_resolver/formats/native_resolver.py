from pathlib import Path
import shutil
import tempfile
from py7zz import SevenZipFile


class NativeResolverFromFile:
    def __init__(self, dep_id, identity, fmt_params, retrieval_dir):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.retrieval_dir = Path(retrieval_dir)

    def pre_fetch_process(self):
        """
        with 文で扱える TemporaryDirectory を返す。
        OCIServer はこのフォルダ内に blob をファイル名で保存する。
        """
        return tempfile.TemporaryDirectory(prefix=f"adira_native_{self.dep_id}_")

    def post_fetch_process(self, blob_path):
        """
        blob を native フォーマット仕様に従って
        最終配置先へ移動・展開する。
        """
        dst_root = self.fmt_params.get("dst_root", "native")
        dst_rel = self.fmt_params.get("dst", self.dep_id)
        final_dir = self.retrieval_dir / dst_root / dst_rel
        final_dir.mkdir(parents=True, exist_ok=True)

        transform = self.fmt_params.get("transform")

        if transform is None:
            # 変換なし → blob をそのまま配置
            target = final_dir / blob_path.name
            self._safe_move(blob_path, target)
            return

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
