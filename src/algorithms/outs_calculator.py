from typing import List


class PokerOutsCalculator:
    """포커 아웃(Outs) 계산 클래스"""

    rank_map = {
        'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
        '9': 9, '8': 8, '7': 7, '6': 6,
        '5': 5, '4': 4, '3': 3, '2': 2
    }

    def __init__(self, cards: list[str]):
        """
        cards: 문자열 리스트 예) ['Ah', 'Kd', '7h', '2c', 'Th', '3d', '4s']
        """
        self.cards = cards
        self.nums = self._get_nums(cards)
        self.suits = [c[-1] for c in cards]

    
    def _get_nums(self, cards: list[str]) -> list[int]:
        """카드 리스트 → 숫자 리스트로 변환 (정렬, 중복 제거X)"""
        return sorted([self.rank_map[c[0]] for c in cards])

   
    def outs_flush(self) -> int:
        """플러시 아웃츠 계산"""
        for suit in ['h', 'd', 'c', 's']:
            count = self.suits.count(suit)
            if count == 4:
                return 13 - count  # 예: 9 outs
        return 0

    def outs_straight(self) -> int:
        """스트레이트 아웃츠 계산"""
        nums = self.nums.copy()

        # A는 1로도 취급 (A-2-3-4-5)
        if 14 in nums:
            nums.append(1)
        nums = sorted(set(nums))

        # 오픈엔드 스트레이트 (양끝 오픈)
        for i in range(len(nums) - 3):
            if nums[i+3] - nums[i] == 3 and len(set(nums[i:i+4])) == 4:
                return 8

        # 인사이드 스트레이트 (한 칸 비어있음)
        for i in range(len(nums) - 4):
            window = nums[i:i+5]
            missing = [x for x in range(window[0], window[-1] + 1) if x not in window]
            if len(missing) == 1:
                return 4

        return 0

    def outs_triple(self) -> int:
        """트리플(세 장 만들기) 아웃츠 계산"""
        nums = self.nums
        unique_nums = set(nums)

        outs = 0
        for num in unique_nums:
            cnt = nums.count(num)
            if cnt == 2:
                outs = 2  # 남은 2장 중 1장 더 필요
        return outs

    def outs_fullhouse(self) -> int:
        """풀하우스 아웃츠 계산"""
        nums = self.nums
        unique_nums = set(nums)
        outs = 0

        for num in unique_nums:
            cnt = nums.count(num)
            if cnt >= 3:
                for other in unique_nums:
                    if other != num:
                        remaining = 2 - nums.count(other)
                        if remaining == 1:
                            outs += 4 - nums.count(other)
            elif cnt == 2:
                outs = 4
        return outs

    def outs_four_of_a_kind(self) -> int:
        """포카드 아웃츠 계산"""
        nums = self.nums
        unique_nums = set(nums)
        outs = 0

        for num in unique_nums:
            cnt = nums.count(num)
            if cnt == 3:
                outs += 4 - cnt
        return outs

    
    def total_outs(self) -> dict[str, int]:
        """모든 아웃 종류를 한 번에 계산"""
        return {
            "flush": self.outs_flush(),
            "straight": self.outs_straight(),
            "triple": self.outs_triple(),
            "fullhouse": self.outs_fullhouse(),
            "four_of_a_kind": self.outs_four_of_a_kind(),
        }
