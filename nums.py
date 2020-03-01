import math
def shorten(number, signs=["K", "M", "B", "T", "Qd", "Qnt", "Sxt", "Spt", "O", "N", "D", "DuoD"], base=3):
	suffix = ""
	outnumber = "{0:,}".format(int(number))
	if getexp(number) >= base:
		try:
			suffix = " {0}".format(signs[int(getexp(number) / base) - 1])
			exp = int(int(getexp(number) / base) * base)
		except:
			suffix = " {0}".format(signs[-1])
			exp = int(len(signs) * base)
		outnumber = "{0:,}".format(int(number / 10**exp))
	return "{0}{1}".format(outnumber, suffix)

def getexp(number):
	try:
		return int(math.log10(math.fabs(number)))
	except:
		return 0
	
def getsign(number):
	try:
		return math.fabs(number) / number
	except:
		return 0
	
def toint(number, base=10):
	try:
		return int(number, base)
	except:
		return None
	
def getval(number, signs=["K", "M", "B", "T", "Qd", "Qnt", "Sxt", "Spt", "O", "N", "D", "DuoD"], base=3):
	number = str(number)
	number = number.replace(",", "").replace(" ", "")
	c = "0"
	i = 0
	while c in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-", "+"]:
		try:
			c = number[i]
		except:
			c = None
		i += 1
	suffix = number[i - 1:].lower()
	number = number[:i - 1]
	
	if suffix in [item.lower() for item in signs]:
		return int(int(number) * 10**(([item.lower() for item in signs].index(suffix) + 1) * base))
	elif suffix == "":
		return int(number)
	else:
		raise Exception("Invalid Number Input")