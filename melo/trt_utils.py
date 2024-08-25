import tensorrt as trt
import torch


## Input preparation
def prepare_emb_inputs(sid, device):
    g = torch.zeros(1, 256, 1).to(device)
    tensors = {
        "inputs": {
            "sid": sid
        },
        "outputs": {
            "g": g
        }
    }

    return tensors

def prepare_enc_p_inputs(x, x_lengths, tone, language, bert, ja_bert, g, x_out, m_p, logs_p, x_mask):
    tensors = {
        'inputs': {
            "x": x,
            "x_lengths": x_lengths,
            "t": tone,
            "language": language,
            "bert_0": bert,
            "bert_1": ja_bert,
            "g": g
        },
        'outputs': {
            "x_out": x_out,
            "m_p": m_p,
            "logs_p": logs_p,
            "x_mask": x_mask
        }
    }


    return tensors

def prepare_sdp_inputs(x, x_mask, g, noise_scale, device):
    logw = torch.zeros(1,1,x_mask.shape[-1]).to(device)

    print(f"SDP X Shape: {x.shape}")

    tensors = {
        "inputs": {
            "x": x,
            "x_mask": x_mask,
            "g": g,
            "noise_scale": noise_scale
        },
        "outputs": {
            "logw": logw
        }
    }

    return tensors

def prepare_dp_inputs(x, x_mask, g, device):
    logw = torch.zeros(1,1,x_mask.shape[-1]).to(device)

    tensors = {
        "inputs": {
            "x": x,
            "x_mask": x_mask,
            "g": g,
        },
        "outputs": {
            "logw": logw
        }
    }

    return tensors

def prepare_flow_inputs(z_p, y_mask, g, device):
    z = torch.zeros(z_p.shape).to(device)
    tensors = {
        "inputs": {
            "z_p": z_p,
            "y_mask": y_mask,
            "g": g,
        },
        "outputs": {
            "z": z
        }
    }

    return tensors


def prepare_dec_inputs(z_in, g, device):
    out = torch.zeros(1, 1, z_in.shape[-1]*512).to(device)

    tensors = {
        "inputs": {
            "z_in": z_in,
            "g": g,
        },
        "outputs": {
            "o": out
        }
    }

    return tensors

## Engine excution
logger = trt.Logger(trt.Logger.VERBOSE)

def load_engine(engine_filepath):
    with open(engine_filepath, "rb") as f, trt.Runtime(logger) as runtime:
        engine = runtime.deserialize_cuda_engine(f.read())
    return engine

def is_dimension_dynamic(dim):
    return dim is None or dim <= 0


def is_shape_dynamic(shape):
    return any([is_dimension_dynamic(dim) for dim in shape])


def run_trt_engine(context, engine, tensors):
    bindings_name = []

    for i in engine:
        bindings_name.append(i)


    bindings = [None]*engine.num_io_tensors

    idx = 0
    for name,tensor in tensors['inputs'].items():
        bindings[idx] = tensor.data_ptr()
        
        if is_shape_dynamic(context.get_tensor_shape(name)):
            context.set_input_shape(name, tensor.shape)
        elif is_shape_dynamic(engine.get_tensor_shape(name)):
            context.get_tensor_shape(name)

        idx += 1

    for name,tensor in tensors['outputs'].items():
        # idx = engine.get_tensor_location(name)
        bindings[idx] = tensor.data_ptr()
        idx += 1

    context.execute_v2(bindings=bindings)