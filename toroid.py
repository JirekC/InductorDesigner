import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pickle
import webbrowser
import math

def text2basic(text, power) :
    """Converts string representation of enginering value to basic physical unit. 

    ### Args:
        - text (str): input string in format eg: "12.5kHz"
        - power (float): power of basic unit eg 2 for m-square, 3 for cubic ...

    ### Raises:
        - ValueError: No of unknown unit or multiplier is specified.

    ### Returns:
        pair:
        - float: value converted to basic-unit
        - str: basic physical unit on value
    """
    retval = 1.0
    unit = ""
    UNITS = ('Hz', 'm', 'A', 'V', 'H') # Hertz, meter, Amper, Volt, Henry
    MULTIPLIERS = {'p':1.0e-12, 'n':1.0e-9, 'u':1.0e-6, 'm':1.0e-3, 'c':1.0e-2, 'd':1.0e-1, '':1.0, 'k':1.0e3, 'M':1.0e6, 'G':1.0e9}
    
    text = text.replace(" ", "") # remove all whitespaces
    text = text.replace(",", ".")

    unit_present = False
    for u in UNITS :
        if text[-len(u):] == u :
            unit_present = True
            unit = u
            text = text[0:len(text) - len(u)] # remove unit from string
            break # for
    # known physical unit found, try to find multiplier
    if unit_present :
        for m in MULTIPLIERS :
            if m == '' :
                continue
            if text[-len(m):] == m :
                retval = MULTIPLIERS[m]
                text = text[0:len(text) - len(m)] # remove multiplier from string
                break # for

    num = float(text) # can raise error if unknown physical unit / multiplier entered
    retval = num * (retval ** power)

    return retval, unit

def check_entry(e, unit, power) :
    """Checks if text in Entry has valid physical unit and is valid number. Changes text color to red if not.

    ### Args:
        - e (ttk.Entry): Entry Widget with text to be converted
        - unit (str): physical unit eg "Hz"
        - power (float): power of basic unit eg 2 for m-square, 3 for cubic ...

    ### Raises:
        - ValueError: Not-convertible string entered
        - ValueError: Unexpected physical unit entered

    ### Returns:
        - float: value converted to basic-unit
    """
    try :
        value, u = text2basic(e.get(), power)
    except:
        e.configure(bg='red')
        raise ValueError(f"Invalid input: '{e.get()}'")
    if u != unit :
        e.configure(bg='red')
        raise ValueError(f"Expected physical unit '{unit}' but '{u}' was entered")
    return value

def calculate_all() :
    try:
        # toroidal core
        out_dia = check_entry(e_OD, "m", 1)
        inn_dia = check_entry(e_ID, "m", 1)
        height = check_entry(e_HT, "m", 1)
        ef_area = check_entry(e_Ae, "m", 2)
        ef_length = check_entry(e_le, "m", 1)
        # wire
        wire_dia = check_entry(e_wire_D, "m", 1)
        wire_ro = check_entry(e_wire_ro, "", 1)
        # inductor / converter
        v_in = check_entry(e_Vin, "V", 1)
        v_out = check_entry(e_Vout, "V", 1)
        i_out = check_entry(e_Iout, "A", 1)
        freq = check_entry(e_freq, "Hz", 1)
        turns = check_entry(e_N, "", 1)
        induct = check_entry(e_L, "H", 1)
    except:
        return False
    
    # converter
    duty_cycle = v_out / v_in
    t_on = duty_cycle / freq
    t_off = 1.0 / freq - t_on
    d_i = (v_out * t_off) / induct # ripple
    # or d_i = ((v_in - v_out) * t_on) / induct
    i_pk = 0.5 * d_i + i_out

    # inductor core - peak values
    b_tesla = ((v_in - v_out) * t_on) / ( 2.0 * ef_area * turns) # half-wave of hyst. loop
    n_amp_m = (turns * i_pk) / ef_length

    # wire loss
    wire_area = math.pi * wire_dia * 0.25
    wire_ohm_per_m = wire_ro / wire_area
    # TODO: wire length + power loss

    # create HTML report
    html = f"""<html> 
<head> 
<title>Inductor design report</title>
<style>
table, th, td {{
  border: 0px solid black;
  border-collapse: collapse;
  padding-left: 10px;
  padding-right: 10px;
}}
</style>
</head> 
<body>
<h2>Synchronous buck converter</h2>
<p>Toroidal core <b>{core_name}</b> with single-layer winding.</p>
<table>
<tr><td>Input voltage</td><td><b>Vin</b></td><td>{v_in:.1f} V</td></tr>
<tr><td>Output voltage</td><td><b>Vout</b></td><td>{v_out:.1f} V</td></tr>
<tr><td>Output current</td><td><b>Iout</b></td><td>{i_out:.3f} A</td></tr>
<tr><td>Frequency</td><td><b>f</b></td><td>{freq:.0f} Hz</td></tr>
<tr><td>Duty cycle</td><td><b>D.C.</b></td><td>{(duty_cycle*1e2):.1f} %</td></tr>
<tr><td>Ripple current</td><td><b>ΔI</b></td><td>{d_i:.3f} A</td></tr>
<tr><td>Peak current</td><td><b>Ipk</b></td><td>{i_pk:.3f} A</td></tr>
<tr><td>Expected inductor value</td><td><b>L</b></td><td>{(induct*1e6):.1f} uH</td></tr>
<tr><td>Peak flux density</td><td><b>Bpk</b></td><td>{b_tesla:.4f} T</td><td>({(b_tesla*1e4):.0f} gauss)</td></tr>
<tr><td>Peak magnetizing force</td><td><b>N</b></td><td>{n_amp_m:.0f} A/m</td><td>({(n_amp_m*4.0*math.pi/1e3):.1f} oersteds)</td></tr>
</table>
<p>
Permeability will decrease from initial value. Please consult 'permeability vs magnetizing force' curve from datasheet.
Than update expected L value and calculate again. Do 2 or 3 iterations to get closer to the real values.
</p>
<p>
Consult material datasheet to determine core loss (W/m^3 times core volume).
</p>
</body> 
</html> 
"""
    
    try:
        with open("inductor.html", "w") as f :
            f.write(html)
    except:
        messagebox.showerror(title=None, message="Can't write to output file 'inductor.html'")
        return False

    webbrowser.open("inductor.html")

    return True

###########
# HELPERS #
###########

def entry_color_reset(e) :
    e.configure(bg='white')
    return True

def entry_set_text(e, text):
    try:
        e.delete(0, tk.END)
        e.insert(0, text)
    except:
        pass
    return

def load_cfg() :
    try:
        with open("toroid.configfile", "rb") as f :
            cfg = pickle.load(f)
    except:
        print("No config file found.")
        return False
    entry_set_text(e_OD, cfg.get('e_OD'))
    entry_set_text(e_ID, cfg.get('e_ID'))
    entry_set_text(e_HT, cfg.get('e_HT'))
    entry_set_text(e_Ae, cfg.get('e_Ae'))
    entry_set_text(e_le, cfg.get('e_le'))
    entry_set_text(e_wire_D, cfg.get('e_wire_D'))
    entry_set_text(e_wire_ro, cfg.get('e_wire_ro'))
    entry_set_text(e_Vin, cfg.get('e_Vin'))
    entry_set_text(e_Vout, cfg.get('e_Vout'))
    entry_set_text(e_Iout, cfg.get('e_Iout'))
    entry_set_text(e_freq, cfg.get('e_freq'))
    entry_set_text(e_N, cfg.get('e_N'))
    entry_set_text(e_L, cfg.get('e_L'))
    return True
    
def save_cfg() :
    cfg = {
        'e_OD': e_OD.get(),
        'e_ID': e_ID.get(),
        'e_HT': e_HT.get(),
        'e_Ae': e_Ae.get(),
        'e_le': e_le.get(),
        'e_wire_D': e_wire_D.get(),
        'e_wire_ro': e_wire_ro.get(),
        'e_Vin': e_Vin.get(),
        'e_Vout': e_Vout.get(),
        'e_Iout': e_Iout.get(),
        'e_freq': e_freq.get(),
        'e_N': e_N.get(),
        'e_L': e_L.get(),
    }
    try:
        with open("toroid.configfile", "wb") as f :
            pickle.dump(cfg, f, pickle.HIGHEST_PROTOCOL)
    except:
        print("Can't write config file!")
    win.destroy()
    return False


################
# MAIN PROGRAM #
################

win = tk.Tk()

###############
# TOROID DIMS #
###############

# entry left-labels
tk.Label(win, text="OD").grid(sticky=tk.E)
tk.Label(win, text="ID").grid(sticky=tk.E)
tk.Label(win, text="HT").grid(sticky=tk.E)
tk.Label(win, text="Ae").grid(sticky=tk.E)
tk.Label(win, text="le").grid(sticky=tk.E)

# entries
e_OD = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_OD))
e_OD.grid(row=0, column=1, padx=5, pady=5)
e_ID = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_ID))
e_ID.grid(row=1, column=1, padx=5, pady=5)
e_HT = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_HT))
e_HT.grid(row=2, column=1, padx=5, pady=5)
e_Ae = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_Ae))
e_Ae.grid(row=3, column=1, padx=5, pady=5)
e_le = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_le))
e_le.grid(row=4, column=1, padx=5, pady=5)

# entry right-labels
tk.Label(win, text="").grid(row=0, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=1, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=2, column=2, sticky=tk.W)
tk.Label(win, text="^2").grid(row=3, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=4, column=2, sticky=tk.W)

# image
pi_toroid = tk.PhotoImage(file="img/toroid_dim.png")
i_toroid = tk.Label(image=pi_toroid).grid(row=0, column=3, rowspan=5, padx=5, pady=5)

#############
# WIRE DIMS #
#############

# entry left-labels
tk.Label(win, text="==WIRE PARAMS==").grid(columnspan=4, sticky=tk.W)
tk.Label(win, text="Dia").grid(sticky=tk.E)
tk.Label(win, text="Resistivity").grid(sticky=tk.E)

# entries
e_wire_D = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_wire_D))
e_wire_D.grid(row=6, column=1, padx=5, pady=5)
e_wire_ro = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_wire_ro))
e_wire_ro.grid(row=7, column=1, padx=5, pady=5)

# entry right-labels
tk.Label(win, text="").grid(row=6, column=2, sticky=tk.W)
tk.Label(win, text="Ω•m").grid(row=7, column=2, sticky=tk.W)

# results
#tk.Label(win, text="Area = xx mm^2").grid(row=5, column=3, padx=10, sticky=tk.W)
#tk.Label(win, text="R = xx Ω").grid(row=6, column=3, padx=10, sticky=tk.W)
#tk.Label(win, text="Power loss = xx W").grid(row=7, column=3, padx=10, sticky=tk.W)

############
# INDUCTOR #
############

# entry left-labels
tk.Label(win, text="==INDUCTOR / CONVERTER PARAMS==").grid(columnspan=4, sticky=tk.W)
tk.Label(win, text="Vin").grid(sticky=tk.E)
tk.Label(win, text="Vout").grid(sticky=tk.E)
tk.Label(win, text="Iout").grid(sticky=tk.E)
tk.Label(win, text="freq").grid(sticky=tk.E)
tk.Label(win, text="Turns").grid(sticky=tk.E)
tk.Label(win, text="L").grid(sticky=tk.E) # expected

# entries
e_Vin = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_Vin))
e_Vin.grid(row=9, column=1, padx=5, pady=5)
e_Vout = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_Vout))
e_Vout.grid(row=10, column=1, padx=5, pady=5)
e_Iout = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_Iout))
e_Iout.grid(row=11, column=1, padx=5, pady=5)
e_freq = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_freq))
e_freq.grid(row=12, column=1, padx=5, pady=5)
e_N = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_N))
e_N.grid(row=13, column=1, padx=5, pady=5)
e_L = tk.Entry(win,width=10, validate='key', vcmd=lambda:entry_color_reset(e_L))
e_L.grid(row=14, column=1, padx=5, pady=5)

# entry right-labels
tk.Label(win, text="").grid(row=9, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=10, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=11, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=12, column=2, sticky=tk.W)
tk.Label(win, text="").grid(row=13, column=2, sticky=tk.W)
tk.Label(win, text="(expect.)").grid(row=14, column=2, sticky=tk.W)

# results
#tk.Label(win, text="Bpk = xyz T").grid(row=9, column=3, padx=10, sticky=tk.W)
#tk.Label(win, text="Npk = xyz A•m").grid(row=10, column=3, padx=10, sticky=tk.W)

# image
pi_buck = tk.PhotoImage(file="img/sync_buck.png")
i_buck = tk.Label(image=pi_buck).grid(row=9, column=3, rowspan=6, padx=5, pady=5)

###################
# MASTER'S BUTTON #
###################

tk.Button(win, text="Calc it!", command=lambda:calculate_all()).grid(row=15, column=1, sticky=tk.W, padx=5, pady=5)

load_cfg()
win.protocol("WM_DELETE_WINDOW", save_cfg)
win.mainloop()
