import re

file_path = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1.md"

with open(file_path, 'r') as f:
    content = f.read()

# I noticed the author for STL-63325 was listed as Mike Wilkins in the table, but the commit shows Bob Cernohous.
content = content.replace('| [STL-63325](https://cornelisnetworks.atlassian.net/browse/STL-63325) | Libfabric | Remove #if 0 dead code | Mike Wilkins |',
                          '| [STL-63325](https://cornelisnetworks.atlassian.net/browse/STL-63325) | Libfabric | Remove #if 0 dead code | Bob Cernohous |')

with open(file_path, 'w') as f:
    f.write(content)
