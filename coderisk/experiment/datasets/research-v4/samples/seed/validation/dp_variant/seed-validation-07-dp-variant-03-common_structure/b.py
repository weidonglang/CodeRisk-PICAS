def common_val_dp_variant(values):
    count = 0
    for item in values:
        if item:
            count += 1
    return count + 7
