

# 임시 카드 구현

rank_map = {'A':14, 'K':13, 'Q':12, 'J':11, 'T':10,
            '9':9, '8':8, '7':7, '6':6, '5':5, '4':4, '3':3, '2':2}

def get_nums(cards):
    """카드 리스트 → 숫자 리스트로 변환, 중복 제거, 정렬"""
    nums = sorted([rank_map[c[0]] for c in cards])
    return nums

def outs_flush(cards):
    """
    cards: 문자열 리스트, 예) ['Ah', '7h', '2h', '9h', 'Th', '3d', '4s']
    플러시 아웃츠 계산 코드

    """
    suits = [card[-1] for card in cards]  # 각 카드의 무늬만 추출
    for suit in ['h', 'd', 'c', 's']:     # 하트, 다이아, 클럽, 스페이드
        if suits.count(suit) == 4:        # 같은 무늬 4장 있으면 
            return 13 - suits.count(suit) # 플러시 아웃츠 리턴(9)
    return 0

def outs_straight(cards):
    """
    cards: 문자열 리스트, 예) ['Ah', 'Kd', 'Qh', 'Jc', 'Th', '2s', '3d']
    스트레이트 아웃츠 계산 코드

    """
    nums = get_nums(cards)

    # A(14)를 1로도 취급 (A-2-3-4-5 스트레이트)
    if 14 in nums:
        nums.append(1)

    # 연속된 4개 숫자 존재 여부 확인(오픈엔드 스트레이트 아웃츠 계산)
    for i in range(len(nums) - 3):
        if nums[i+3] - nums[i] == 3 and len(set(nums[i:i+4])) == 4:
            return 8

    # 중간이 비어있는 스트레이트(인사이드 스트레이트 계산)
    for i in range(len(nums) - 4):
        window = nums[i:i+5]
        missing = [x for x in range(window[0], window[-1]+1) if x not in window]
        if len(missing) == 1:
            return 4
        
    return 0

def outs_triple(cards):
    """
    cards: 문자열 리스트, 예) ['Ah', 'Ad']
    이미 같은 카드 2장이 있다고 가정 
    트리플 아웃츠 계산 코드
    
    """
    # 카드 숫자 변환
    rank_map = {'A':14, 'K':13, 'Q':12, 'J':11, 'T':10,
                '9':9, '8':8, '7':7, '6':6, '5':5, '4':4, '3':3, '2':2}
    nums = [rank_map[c[0]] for c in cards]

    # 중복 제거 → 숫자별로 한 번씩만 계산
    unique_nums = set(nums)

    outs = 0
    for num in unique_nums:
        cnt = nums.count(num)
        if cnt == 2:
            outs = 2
    return outs

def outs_fullhouse(cards):
    """
    cards: 현재 핸드 + 보드 카드 전체 리스트, 예) ['Ah', 'Ad', 'Ac', '2d', '2h', '3s']
    풀하우스 아웃츠 계산 코드

    """
    nums = get_nums(cards)

    unique_nums = set(nums)
    outs = 0

    for num in unique_nums:
        cnt = nums.count(num)
        if cnt >= 3:
            # 트리플이 이미 있는 경우 → 다른 숫자 2장 나와야 풀하우스
            for other in unique_nums:
                if other != num:
                    # 페어를 만들기 위해 필요한 카드 수
                    remaining = 2 - nums.count(other)
                    if remaining == 1: #페어 까지 1장 남았을 때
                        # 실제 덱에 남아 있는 카드 수 = 4 - 이미 나온 카드 수
                        outs += 4 - nums.count(other)
        elif cnt == 2:
            # 페어인 경우 → 투페어 기준으로 풀하우스 아웃츠 계산
            outs = 4
    return outs

def outs_four_of_a_kind(cards):
    """
    cards: 문자열 리스트, 예) ['Ah', 'Ad', 'Ac', '2d', '3s']
    포카드 아웃츠 계산 코드
    
    """
    nums = get_nums(cards)

    unique_nums = set(nums)
    outs = 0

    for num in unique_nums:
        cnt = nums.count(num)
        if cnt == 3:  
            outs += 4 - cnt  
    return outs
