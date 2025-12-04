import argparse

from . import __version__, searcher


def search(database, target_composition, **options):
    best_matches, elapsed = searcher.find_best_matches(database, target_composition, **options)
    print(f'計算匹配度用時: {elapsed}')

    for match in best_matches:
        match_percentage, combination, dosages = match

        combined_composition = {}
        for dosage, formula in zip(dosages, combination):
            for herb, amount in database[formula].items():
                combined_composition[herb] = combined_composition.get(herb, 0) + dosage * amount

        herbs_amount = sorted(combined_composition.items(), key=lambda item: (item[0] not in target_composition, item[0]))

        missing_herbs = {
            herb: amount
            for herb in target_composition
            if (amount := target_composition.get(herb)) and not combined_composition.get(herb)
        }

        combination_str = ', '.join(f'{formula}{dosage:.1f}' for formula, dosage in zip(combination, dosages))
        print(f'匹配度: {match_percentage:.2f}%，組合: {combination_str}')
        for herb, amount in herbs_amount:
            if herb in target_composition:
                herb = f'**{herb}**'
            print(f'    {herb}: {amount:.2f}')

        if missing_herbs:
            print('尚缺藥物：')
            for herb in missing_herbs:
                print(f'    {herb}')
        else:
            print('所有目標藥材已被完全匹配。')
        print('\n')


def cmd_search(args):
    try:
        database = searcher.load_formula_database(args.database)
    except OSError:
        print(f'無法載入資料庫檔案: {args.database}')
        return

    print(f'方劑數量:{len(database.keys())}')

    target_composition = {}
    excludes = None
    if len(args.items) > 1:
        all_herbs = set()
        for formula in database.values():
            if len(formula) > 1:
                all_herbs |= formula.keys()

        unknown_herbs = []
        for herb, amount in args.items:
            if herb not in all_herbs:
                unknown_herbs.append(herb)
                continue
            target_composition[herb] = target_composition.get(herb, 0) + amount
        if unknown_herbs:
            print(f'資料庫尚未收錄以下藥物：{", ".join(unknown_herbs)}')
            return
    else:
        formula_name, input_dosage = args.items[0]
        if formula_name not in database:
            print('資料庫尚未收錄此方劑。')
            return
        for herb, amount in database[formula_name].items():
            target_composition[herb] = input_dosage * amount
        excludes = {formula_name}

    search(database, target_composition,
           excludes=excludes, penalty_factor=args.penalty, top_n=args.num)


def parse_item(value):
    name, sep, dose = value.partition(':')
    return name, float(dose)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="""搜尋中藥配方的替代組合。""",
    )
    parser.add_argument(
        '--version', action='version', version=f'{__package__} {__version__}',
        help="""顯示版本資訊並離開""",
    )
    subparsers = parser.add_subparsers(
        metavar='COMMAND',
        help="""執行子命令，可用如 %(prog)s search -h 取得相關說明""",
    )

    parser_search = subparsers.add_parser(
        'search', aliases=['s'],
        help="""搜尋中藥配方的替代組合""",
        description="""搜尋中藥配方的替代組合。""",
    )
    parser_search.set_defaults(func=cmd_search)
    parser_search.add_argument(
        'items', metavar='NAME:DOSE', nargs='+', type=parse_item, action='store',
        help="""要搜尋的品項及劑量。可輸入一個複方或多個中藥，例如 '補中益氣湯:3.0' 或 '人參:3.0 茯苓:2.5'""",
    )
    parser_search.add_argument(
        '-p', '--penalty', metavar='FACTOR', default=2.0, type=float, action='store',
        help="""未配對項目的懲罰因子 (預設: %(default)s)""",
    )
    parser_search.add_argument(
        '-n', '--num', metavar='N', default=5, type=int, action='store',
        help="""最佳匹配結果顯示筆數 (預設: %(default)s)""",
    )
    parser_search.add_argument(
        '-d', '--database', metavar='FILE', default=searcher.DEFAULT_DATAFILE, action='store',
        help="""使用自訂的資料庫檔案 (預設: %(default)s)""",
    )

    return parser.parse_args(argv)


def main():
    args = parse_args()

    if not hasattr(args, 'func'):
        parse_args(['-h'])
        return

    args.func(args)
