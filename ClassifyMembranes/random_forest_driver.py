#-----------------------------
#Random Forest Feature Elimination Driver
#Daniel Miron
#6/18/2013
#
#Creates Command Line Arguments for Running eliminate_features
#-----------------------------



script_loc = r"C:\Users\DanielMiron\rhoana\ClassifyMembranes\eliminate_features.py"
image_loc = r"C:\Users\DanielMiron\Documents\third_round"
features = range(98)

for feat in features:
    print "%run" + " " + script_loc + " " + image_loc + " " + str(feat)

feature_groups = [range(21), range(22,32), range(34,42), range(49, 59),
                range(59, 69), range(69, 79), range(79, 89), range(89, 94),
                range(94,98), range(89, 98)]
                
for group in feature_groups:
    feat_str = ""
    for feat in group:
        feat_str += str(feat) + ","
    print "%run" + " " + script_loc + " " + image_loc + " " + feat_str[:-1]
