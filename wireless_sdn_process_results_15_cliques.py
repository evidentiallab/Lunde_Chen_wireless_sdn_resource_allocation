
res = '3 4	4	4	5	7	8	8	8	10	10	10	11	11	11 ' + \
'11.76757813	17.91992188	20.01953125	19.43359375	20.8984375	30.22460938	43.75	41.30859375	41.55273438	42.91992188	41.40625	24.90234375	42.28515625	42.67578125	39.94140625 ' + \
'9.130859375	13.96484375	15.8203125	15.08789063	16.55273438	36.57226563	36.328125	25.87890625	26.51367188	53.80859375	52.39257813	33.69140625	64.453125	65.47851563	62.06054688'

sp = res.split()
a = [int(sp[i]) for i in range(15)]
b = [float(sp[i]) for i in range(15, 30)]
c = [float(sp[i]) for i in range(30, 45)]
d = []
for i in range(15):
    d.append((a[i], b[i] - c[i]))
print(d)

fa = open('./wireless_sdn_iwqos/interference/15_cliques_small.txt', "w")
for i in range(5):
    # fa.write(str(d[i][0]) + ' ' + str(d[i][1]) + '\n')
    fa.write(str(d[i][1]) + ' ')
fa.close()

fa = open('./wireless_sdn_iwqos/interference/15_cliques_medium.txt', "w")
for i in range(5, 9):
    # fa.write(str(d[i][0]) + ' ' + str(d[i][1]) + '\n')
    fa.write(str(d[i][1]) + ' ')
fa.close()


fa = open('./wireless_sdn_iwqos/interference/15_cliques_large.txt', "w")
for i in range(9, 15):
    # fa.write(str(d[i][0]) + ' ' + str(d[i][1]) + '\n')
    fa.write(str(d[i][1]) + ' ')
fa.close()


