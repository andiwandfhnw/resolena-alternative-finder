import shlex

FEATURES = {'-msse4.2':'sse4_2', '-mavx':'avx', '-mavx2':'avx2',
            '-mfma':'fma', '-mf16c':'f16c', '-mbmi2':'bmi2'}
BASELINE = {'-march=x86-64', '-mtune=generic'}


def verify_flags(commands, cpu_flags):
    switches = set(); backend = False
    for entry in commands:
        backend = backend or 'ggml-cpu' in entry['file']
        args = entry.get('arguments') or shlex.split(entry['command'])
        for arg in args:
            if arg.startswith('-m'):
                if arg not in BASELINE and arg not in FEATURES:
                    raise RuntimeError('Unapproved architecture switch: '+arg)
                if arg in FEATURES and FEATURES[arg] not in cpu_flags:
                    raise RuntimeError('Host lacks '+FEATURES[arg])
                switches.add(arg)
    if not backend:
        raise RuntimeError('CPU backend compile commands absent')
    return {'passed':True, 'effective_architecture_switches':sorted(switches),
            'required_host_features':sorted(FEATURES[s] for s in switches if s in FEATURES),
            'compile_commands_checked':len(commands), 'native_flags_absent':True}
