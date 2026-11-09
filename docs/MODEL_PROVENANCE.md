# Model provenance and security

Upstream Wiki implementation: `alirzx/organizational-wiki-intelligence-doc-scanner`, `app/modules/stamp_signature/{rfdetr_backend.py,adapter.py,service.py}`. Upstream model: `bluecopa/rf-detr-stamp-signature-detector`. Architecture: RF-DETR Base (DINOv2 backbone). The model card describes Apache-2.0 licensing and published benchmark scores; these are **not SuperApp validation results**.

Pin: revision `c59fd4f451b254501700a56c7769f1a3d788c753`, filename `checkpoint_best_ema.pth`, SHA256 `3a831ae093be64a01a4d9c635dc6071ad7c43c3e95c3da0b33a17351df1e7909`, roughly 368,825,120 bytes. The pin and SHA were taken from the source Wiki configuration and the Hugging Face file's public LFS digest. If upstream changes weights, update the revision, digest, class ID contract, and tests together through code review.

A dedicated `model-setup` service downloads exactly this revision, verifies the SHA256, installs atomically and writes `manifest.json`. A verified model is reused after container recreation. Production startup verifies the manifest and SHA256 again and never requests network access. Do not run untrusted checkpoints: `.pth` deserialization can execute pickle payloads, so SHA pinning establishes *artifact identity*, not an absolute guarantee of safety.

Class IDs 0=stamp and 1=signature are returned; checkbox_checked/checkbox_unchecked (IDs 2/3) are discarded. No OCR, authentication of signatures, or verification of legal document validity.

RF-DETR Base is **not an ultra-small model**: 369 MB on disk and potentially multiple gigabytes of working memory depending on Torch. Measure peak RSS, startup, p50/p95 latency, CPU utilization, recall and precision on target hardware. Quantization or a different backbone would require new model validation rather than an unverified substitution.
