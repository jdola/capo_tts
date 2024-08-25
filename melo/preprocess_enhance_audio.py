import gradio as gr
import torch
import torchaudio
import torch.multiprocessing as mp
import os
import json
import traceback as tb
from glob import glob
import time

from resemble_enhance.enhancer.inference import denoise, enhance
import argparse

def worker(device_queue, device, solver='midpoint', nfe=64, tau=0.5, denoising=True):
    solver = solver.lower()
    nfe = int(nfe)
    lambd = 0.9 if denoising else 0.1
    while True:
        data = device_queue.get()
        if data is None:
            break

        in_path, save_path = data["fpath"], data["save_fpath"]
        try:
            dwav, sr = torchaudio.load(in_path)
            dwav = dwav.mean(dim=0)

            wav2, new_sr = enhance(dwav, sr, device, nfe=nfe, solver=solver, lambd=lambd, tau=tau)

            # wav1 = wav1.cpu().numpy()
            wav2 = wav2.cpu().numpy()

            torchaudio.save(save_path, torch.FloatTensor(wav2).unsqueeze(0), new_sr)

        except:
            tb.print_exc()
            print(in_path)
            pass

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--input_dir", type=str, help="Path to the input directory")
        parser.add_argument("--output_dir", type=str, help="Path to the output directory")
        parser.add_argument("--n_worker", type=int, default=10, help="Number of worker processes")
        args = parser.parse_args()
        print(args)
        torch.multiprocessing.set_start_method('spawn')

        data_queue = mp.Queue()
        n_worker = int(args.n_worker)

        # Send data to the worker processes 
        audio_file_paths = glob(f"{args.input_dir}/*.wav", recursive=True)
        print(len(audio_file_paths))
        for fp in audio_file_paths:
            save_fpath = fp.replace(args.input_dir, args.output_dir)
            if not os.path.isfile(save_fpath):
                data_queue.put({
                    "fpath": fp,
                    "save_fpath": save_fpath
                })

        # Spawn processes
        processes = []
        if torch.cuda.is_available():
            num_gpus = torch.cuda.device_count()
            devices = [f"cuda:{i}" for i in range(num_gpus)]
        else:
            devices = ["cpu"]
        for i in range(n_worker):
            device = devices[i % len(devices)]
            p = mp.Process(target=worker, args=(data_queue,device,))
            p.start()
            processes.append(p)
            time.sleep(2)

        # Signal the processes to exit
        for _ in range(n_worker):
            data_queue.put(None)

        # Wait for all processes to finish
        for p in processes:
            p.join()
        print("All processes were succeeded.")

    except KeyboardInterrupt:
        print("Interrupt received! Shutting down.")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("All processes were successfully terminated.")