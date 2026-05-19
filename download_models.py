"""下载 FunASR 语音识别模型到 model/ 目录"""
import subprocess
import sys
from pathlib import Path

MODELS = [
    "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "iic/punc_ct-transformer_cn-en-common-vocab471067-large",
]

MODEL_DIR = Path(__file__).parent / "model"


def main():
    print("=" * 50)
    print("  FunASR 语音识别模型下载工具")
    print("=" * 50)
    print()
    print(f"模型将下载到: {MODEL_DIR}")
    print(f"共 {len(MODELS)} 个模型，总计约 2GB")
    print()

    # 检查 modelscope 是否安装
    try:
        import modelscope
    except ImportError:
        print("[提示] 正在安装 modelscope...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "modelscope", "-q"])

    MODEL_DIR.mkdir(exist_ok=True)

    for i, model_id in enumerate(MODELS, 1):
        print(f"\n[{i}/{len(MODELS)}] 下载: {model_id}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "modelscope", "download",
                "--model", model_id,
                "--local_dir", str(MODEL_DIR / model_id.split("/")[-1]),
            ])
            print(f"  [OK] 下载完成")
        except subprocess.CalledProcessError as e:
            print(f"  [错误] 下载失败: {e}")
            print(f"  请手动下载: https://modelscope.cn/models/{model_id}")
            return 1

    print("\n" + "=" * 50)
    print("  全部模型下载完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
