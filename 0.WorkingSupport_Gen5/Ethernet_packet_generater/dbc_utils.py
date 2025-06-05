import pandas as pd

def parse_csv(path):
    df = pd.read_csv(path)
    df = df.dropna(subset=['dbc_Message', 'dbc_Signal'], how='any')
    df = df.fillna('')
    return df

def get_messages(df):
    return sorted(df['dbc_Message'].unique())

def get_signals(df, message):
    df_msg = df[df['dbc_Message'] == message].copy()
    df_msg['dbc_Startbit'] = df_msg['dbc_Startbit'].astype(float)
    df_msg = df_msg[df_msg['dbc_Signal'] != '']
    df_msg = df_msg.sort_values('dbc_Startbit').reset_index(drop=True)
    # Lấy Total length từ cột "Total length" (ưu tiên lấy giá trị đầu tiên)
    total_len = None
    if 'Total length' in df_msg.columns:
        try:
            total_len = int(float(df_msg['Total length'].iloc[0]))
        except Exception:
            total_len = None
    return df_msg, total_len

def calc_signal_raw(val, factor, offset, minv, maxv):
    try:
        val = float(val)
        factor = float(factor) if factor != '' else 1
        offset = float(offset) if offset != '' else 0
        minv = float(minv) if minv != '' else None
        maxv = float(maxv) if maxv != '' else None
        raw = int(round((val - offset) / factor))
        if minv is not None and val < minv:
            raw = int(round((minv - offset) / factor))
        if maxv is not None and val > maxv:
            raw = int(round((maxv - offset) / factor))
        return raw
    except Exception:
        return 0

def build_payload(signals, total_len=None):
    # Tìm bit lớn nhất của các signal
    maxbit = 0
    for sig in signals:
        start = int(float(sig['dbc_Startbit']))
        length = int(float(sig['dbc_Length [bit]']))
        if start + length > maxbit:
            maxbit = start + length
    # Nếu có tổng length của message, dùng nó
    if total_len is not None and total_len > maxbit:
        maxbit = total_len
    nbytes = (maxbit + 7) // 8
    payload = [0] * nbytes

    for sig in signals:
        start = int(float(sig['dbc_Startbit']))
        length = int(float(sig['dbc_Length [bit]']))
        raw = int(sig['raw_value'])
        for i in range(length):
            bitval = (raw >> i) & 1
            bitpos = start + i
            byteidx = bitpos // 8
            bitidx = bitpos % 8
            if sig['dbc_ByteOrder'] == 'Intel':
                payload[byteidx] |= (bitval << bitidx)
            else:
                payload[byteidx] |= (bitval << (7 - bitidx))
    return ''.join(f'{b:02X}' for b in payload)