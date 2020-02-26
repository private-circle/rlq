from rlq import *

sample_qspecs = [

    # Different ways of specifying the field labels (headers)
    # 1: By default, the field labels are shown and the output format is row_wise_dicts
    {
        'select': [C('in-ca:NameOfCompany')],  # Should show {'Name of company': <COMPANY_NAME>}
    },
    # 2: You can choose to use names instead of labels as headers using header_display
    {
        'select': [C('in-ca:NameOfCompany')],
        'header_display': 'name'  # Should show {'in-ca:NameOfCompany': <COMPANY_NAME>}
    },
    # 3: You can explicitly provide headers as a dict
    {
        'select': {'Company Name': C('in-ca:NameOfCompany')}  # Should show {'Company Name': <COMPANY_NAME>}
    },
    # 4: or as tuple
    {
        'select': [('Company Name', C('in-ca:NameOfCompany'))]
    },
    # 5: or as a separate headers key in the query spec
    {
        'select': [C('in-ca:NameOfCompany')],
        'headers': ['Company Name']
    },
    # 6: You can choose to only output the data without the headers as tuples instead of dicts
    {
        'select': [C('in-ca:CorporateIdentityNumber'), C('in-ca:NameOfCompany')],  # Should show (<CIN>, <COMPANY_NAME>)
        'output_format': 'row_wise'
    },
    # 7: The valid output formats are row_wise, row_wise_dicts, row_wise_with_headers, column_wise, column_wise_dicts
    #    and column_wise_with_headers. The default is row_wise_dicts.

    # EXAMPLE QUERIES

    # Get the names of auditors and their dates of signing audit report.
    # Note the dimension condition Ax() >= {'in-ca:AuditorsAxis'}
    # This implies that the dimension in-ca:AuditorsAxis must be present.
    # Without this or any other dimension-related clause, the default dimension condition of
    # Ax() == set() (no dimensions specified) is used.
    {
        'select': [C('in-ca:NameOfAuditFirm'), C('in-ca:DateOfSigningAuditReportByAuditors')],
        'where': [Ax() >= {'in-ca:AuditorsAxis'}],
    },
    # Get a single row for all the auditors of the company.
    # Combine the names using comma and get the signing date for the first auditor
    {
        'select': [Join(C('in-ca:NameOfAuditFirm'), ', '), First(C('in-ca:DateOfSigningAuditReportByAuditors'))],
        'where': [Ax() >= {'in-ca:AuditorsAxis'}],
    },

    # Get the CIN, name and country of all the related parties along with the nature of their relationship
    # for all years. Only include related parties that are companies, not individuals.
    # For ind-as XBRLs, the nature of the relationship comes as the value of the dimension
    # `ind-as:CategoriesOfRelatedPartiesAxis`.
    #
    # Note the expression syntax for boolean operators other than the comparison operators: E(op, OPERAND1, OPERAND2)
    # Supported operators include in, nin (not in), contains, icontains, regex, iregex.
    {
        'select': [C('in-ca:CINOfRelatedParty'), C('ind-as:NameOfRelatedParty'),
                   C('in-ca:CountryOfIncorporationOrResidenceOfRelatedParty'),
                   DL('ind-as:CategoriesOfRelatedPartiesAxis'), FY()],  # DL => DimMemberLabel
        'where': [D('ind-as:CategoriesOfRelatedPartiesAxis').nin(
                    ['ind-as:KeyManagementPersonnelOfEntityOrParentMember', 'ind-as:OtherRelatedPartiesMember'])]
    },

    # Paid up preference capital for current year
    #
    # Sum the value of the field ind-as:ValueOfSharesSubscribedAndFullyPaid
    # where the associated field ind-as:TypeOfShare contains preference

    # Notice the context_groupby argument is changed from the default which is CtxID() to CtxHash()
    # because the 2 fields ind-as:TypeOfShare (duration) and ind-as:ValueOfShares... (instant) are not
    # related by context ID as they have different period types.
    {
        'select': [Sum(C('ind-as:ValueOfSharesSubscribedAndFullyPaid'))],
        'where': [Ax() >= {'ind-as:ClassesOfEquityShareCapitalAxis'},
                  C('ind-as:TypeOfShare').icontains('preference'),
                  FY() == FY.CURR],
        'context_groupby': [CtxHash()],
        'output_format': 'row_wise'
    },

    # Get the paid up preference capital for all years
    {
        'select': [Sum(C('ind-as:ValueOfSharesSubscribedAndFullyPaid')), FY()],
        'where': [Ax() >= {'ind-as:ClassesOfEquityShareCapitalAxis'},
                  C('ind-as:TypeOfShare').icontains('preference')],
        'context_groupby': [CtxHash()],
        'groupby': [FY()]  # Group by FY for the sum aggregation
    }
]


if __name__ == '__main__':
    from pprint import pprint
    import os
    from rlq.rl_utils import load_xbrl_model

    xbrl_samples_dir = '/home/privatecircle/Downloads/XBRL Samples'
    xbrl_model = load_xbrl_model(os.path.join(xbrl_samples_dir, '2019', 'Instance_Bundl.xml'))  # ind-as
    # xbrl_model = load_xbrl_model(os.path.join(
    #     xbrl_samples_dir, '2016', 'L15140MH1988PLC049208-Con-FinancialStatements-2016-03-31.xml'))  # in-gaap
    q_model = QueryExecutor(xbrl_model)
    for i, qspec in enumerate(sample_qspecs, start=1):
        print('Query {}'.format(i))
        print('----------')
        rows = q_model.query(qspec)
        if not rows:
            continue
        pprint(rows)
        print()
