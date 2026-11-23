"""Run with uv run python -m iress_data audit|verify."""

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from .audit import run_audit
from .config import Config


def main() -> None:
    parser = argparse.ArgumentParser(description="IRESS historical source-data audit")
    parser.add_argument("command", choices=["audit", "verify", "build", "package", "verify-package", "release"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--exports", type=Path)
    parser.add_argument("--intermediate", type=Path)
    parser.add_argument("--reports", type=Path)
    parser.add_argument("--force", action="store_true", help="Re-read Excel even if checksums match")
    parser.add_argument("--memory-limit", default="512MB", help="DuckDB memory limit")
    parser.add_argument("--destination",type=Path,help="Handover directory; default dist/thesis_data")
    parser.add_argument("--audit-only",action="store_true",help="Verify the historical audit instead of the processed build")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.from_root(args.root)
    cfg = replace(cfg, memory_limit=args.memory_limit,
                  **{k: getattr(args, k).resolve() for k in ("exports", "intermediate", "reports")
                     if getattr(args, k) is not None})
    if args.command == "audit":
        summary = run_audit(cfg, args.force)
        if summary["input_failures"] or summary["missing_batches"]:
            parser.exit(2, "Audit reports describe incomplete inputs; see audit_summary.json.\n")
    elif args.command == "verify":
        if (cfg.root/"data/processed/build_manifest.json").exists() and not args.audit_only:
            from .processed_validation import verify_processed
            result=verify_processed(cfg)
            print(f"PASS: {result['canonical_rows']:,} canonical observations; {result['raw_source_rows']:,} source rows; all deep checks passed.")
        else:
            from .verify import verify
            for message in verify(cfg):
                print(message)
    elif args.command in ("build","release"):
        from .build import build
        build(cfg)
        if args.command=="release":
            from .handover import package
            package(cfg,args.destination)
    elif args.command=="package":
        from .handover import package
        package(cfg,args.destination)
    elif args.command=="verify-package":
        from .handover import verify_package
        verify_package(args.destination or cfg.root/"dist/thesis_data")


if __name__ == "__main__":
    main()
