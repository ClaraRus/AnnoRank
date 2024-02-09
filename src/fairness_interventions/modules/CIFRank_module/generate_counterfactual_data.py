import pandas as pd
import os


def get_counterfactual_data_real(cur_df, path_causal, args_causal, args_data):
    group_list = [x for x in cur_df[args_data['group']].unique() if x != args_causal['control']]

    mediators = pd.read_csv(os.path.join(path_causal, "identified_mediators.csv"))
    no_mediators = len(mediators) == 0 or str(mediators['mediators'].values[0]) == 'nan'

    new_cols = []
    for med in args_causal['features']:
        if med in mediators['mediators'].values:
            x_res = pd.read_csv(os.path.join(path_causal, med + "~" + args_data['group'] + "-1.csv"))
            counter_g_base = x_res[x_res["Unnamed: 0"] == args_data['group'] + args_causal['control']]["Estimate"].values[0]

            x_shifts = {args_causal['control']: 0}
            for gi in group_list:
                if not args_data['group'] + gi in x_res["Unnamed: 0"].values:
                    x_shifts[gi] = 0
                else:
                    other_g_base = x_res[x_res["Unnamed: 0"] == args_data['group'] + gi]["Estimate"].values[0]
                    x_shifts[gi] = counter_g_base - other_g_base

            feature_shifts = cur_df[args_data['group']].apply(lambda x: x_shifts[x])
            cur_df.loc[:, med + "_fair"] = cur_df[med] + feature_shifts
            new_cols.append(med + "_fair")

        else:
            # variables that are not mediators remain unchanged
            cur_df.loc[:, med + "_fair"] = cur_df[med]
            new_cols.append(med + "_fair")

    if no_mediators:
        # direct effect of the IV on the DV --> we keep the observed X as it is
        y_res = pd.read_csv(os.path.join(path_causal, args_data['score'] + '~' + args_data['group'] + "-1.csv"))
        counter_g_base = y_res[y_res["Unnamed: 0"] == args_data['group'] + args_causal['control']]["Estimate"].values[0]
        y_shifts = {args_causal['control']: 0}
        for gi in group_list:
            if not args_data['group'] + gi in y_res["Unnamed: 0"].values:
                y_shifts[gi] = 0
            else:
                y_shifts[gi] = counter_g_base - y_res[y_res["Unnamed: 0"] == args_data['group'] + gi]["Estimate"].values[0]
    else:
        y_shifts = {args_causal['control']: 0}
        y_shifts_resolve = {args_causal['control']: 0}
        for gi in group_list:
            if not os.path.exists(os.path.join(path_causal, gi + "_med" + ".csv")):
                y_shifts[gi] = 0
                y_shifts_resolve[gi] = 0
            else:
                g_res = pd.read_csv(os.path.join(path_causal, gi + "_med" + ".csv"))
                y_shifts[gi] = -g_res[g_res['Metric'] == 'Total Effect']["Estimate"].values[0]
                y_shifts_resolve[gi] = -g_res[g_res['Metric'] == 'Direct Effect']["Estimate"].values[0]

    cur_df["Y_shift"] = cur_df[args_data['group']].apply(lambda x: y_shifts[x])
    cur_df[args_data['score'] + "_fair"] = cur_df[args_data['score']] + cur_df["Y_shift"]
    new_cols.append(args_data['score'] + "_fair")

    return cur_df
