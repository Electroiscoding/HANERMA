import sys
print("Loading...", flush=True)
from crayon import CrayonVocab
v = CrayonVocab(device="cpu")
v.load_profile("lite")

print(f"vocab_size: {v.vocab_size}", flush=True)
print(f"info: {v.get_info()}", flush=True)
print(f"using_profile: {v.using_profile}", flush=True)
print(f"profile_path: {v.current_profile_path}", flush=True)
print(f"device: {v.device}", flush=True)
print(f"is_gpu: {v.is_gpu}", flush=True)
print(f"is_profile_loaded: {v.is_profile_loaded}", flush=True)

# Check the DAT file
import os
dat_path = v.current_profile_path
print(f"\nDAT file exists: {os.path.exists(dat_path)}", flush=True)
print(f"DAT file size: {os.path.getsize(dat_path)} bytes", flush=True)
