def calctime(minorrank, majorrank, initbonus, itemboost):
	nextrank = 5000 * (8**(majorrank - 1)) * minorrank
	bestdpm = 10 * (7**(majorrank - 1)) * minorrank * (itemboost / 100 + 1)
	
	minutes = 0
	discs = 0
	bonus = initbonus
	while discs < nextrank:
		discs += bestdpm * bonus
		bonus += 1
		if bonus > 1000:
			bonus = 1000
		minutes += 1
	
	return minutes