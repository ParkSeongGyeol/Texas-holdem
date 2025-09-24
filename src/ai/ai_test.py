from rule_based_ai import RuleBasedAI  
from base_ai import Action    

ai = RuleBasedAI("BOT")
# 프리플랍 A-K
ai.hole_cards = ["A♠", "K♥"]
action, amount = ai.make_decision([], 100, 0, [])
print(f"액션: {action.name}, 베팅: {amount}")

# 프리플랍 7-2
ai.hole_cards = ["7♠", "2♠"]
action, amount = ai.make_decision([], 100, 10, [])
print(f"액션: {action.name}, 베팅: {amount}")

# 플랍 이후
ai.hole_cards = ["A♠", "K♥"]
community = ["Q♠", "J♦", "2♣"]
action, amount = ai.make_decision(community, 160, 20, [])
print(f"액션: {action.name}, 베팅: {amount}")