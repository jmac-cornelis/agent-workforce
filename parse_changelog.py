import re
import sys
from collections import OrderedDict

def main():
    input_file = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1 1.txt"
    output_file = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1.md"

    try:
        with open(input_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Convert all STL-XXXXX references to hyperlinks
    def replace_jira(match):
        jira = match.group(0)
        return f"[{jira}](https://cornelisnetworks.atlassian.net/browse/{jira})"

    content = re.sub(r'STL-\d{5}', replace_jira, content)

    # Build the bug table (static data from instructions)
    bug_table = """## Bug Ticket Summary
| Jira ID | Component | Summary | Author |
|---------|-----------|---------|--------|
| [STL-77101](https://cornelisnetworks.atlassian.net/browse/STL-77101) | Driver | Only print perf counters if counted | Nick Child |
| [STL-76477](https://cornelisnetworks.atlassian.net/browse/STL-76477) | Driver | Reapply cport MSI-X interrupt | Dennis Dalessandro |
| [STL-76488](https://cornelisnetworks.atlassian.net/browse/STL-76488) | Driver | Reapply disable lost interrupt timer + additional cport interrupt clears | Dennis Dalessandro |
| [STL-71206](https://cornelisnetworks.atlassian.net/browse/STL-71206) | Driver | Fix firmware update MAD response handling over fabric | Douglas Miller |
| [STL-74848](https://cornelisnetworks.atlassian.net/browse/STL-74848), [STL-76311](https://cornelisnetworks.atlassian.net/browse/STL-76311), [STL-76441](https://cornelisnetworks.atlassian.net/browse/STL-76441) | Driver | Threaded NAPI for IPoIB TX completion (priority inversion fix) | Brian Hwang |
| [STL-76662](https://cornelisnetworks.atlassian.net/browse/STL-76662) | Driver | Make MCTXT tid xarray interrupt safe | Douglas Miller |
| [STL-76676](https://cornelisnetworks.atlassian.net/browse/STL-76676) | Driver | SDMA header optimization bug fixes | Pooja Nara |
| [STL-76747](https://cornelisnetworks.atlassian.net/browse/STL-76747) | Driver | Simplify receive context processing | Ian Simonson |
| [STL-76962](https://cornelisnetworks.atlassian.net/browse/STL-76962) | Driver | Multiple DMS/bulksvc fixes (5 sub-fixes) | Michael Blocksome |
| [STL-76982](https://cornelisnetworks.atlassian.net/browse/STL-76982) | Driver | DMS access unregister rework (4 sub-fixes) | Michael Blocksome, Ian Simonson |
| [STL-76983](https://cornelisnetworks.atlassian.net/browse/STL-76983) | Driver | Switch DMS access unregister to passive-only | Michael Blocksome |
| [STL-76995](https://cornelisnetworks.atlassian.net/browse/STL-76995) | Driver | Multiple MR/bulksvc leak fixes (4 sub-fixes) | Ian Simonson |
| [STL-76999](https://cornelisnetworks.atlassian.net/browse/STL-76999) | Driver | Fix bulksvc_dbg_open unbounded spin-wait deadlock | Michael Blocksome |
| [STL-77001](https://cornelisnetworks.atlassian.net/browse/STL-77001) | Driver | Tone down DMS health timeout log wording | Michael Blocksome |
| [STL-77070](https://cornelisnetworks.atlassian.net/browse/STL-77070) | Driver | Fix use-after-free in cport_req_fn() | Douglas Miller |
| [STL-77078](https://cornelisnetworks.atlassian.net/browse/STL-77078) | Driver | Restrict send scheduling checks to RESET state | Michael Blocksome, Ian Simonson |
| [STL-77027](https://cornelisnetworks.atlassian.net/browse/STL-77027) | HFIFW | Cannot Start Second FM | Paul Davis, Daniel Gailey |
| [STL-76561](https://cornelisnetworks.atlassian.net/browse/STL-76561) | Libfabric | Multiple mm lock / rendezvous fixes (5 sub-fixes) | Bob Cernohous |
| [STL-76778](https://cornelisnetworks.atlassian.net/browse/STL-76778) | Libfabric | Change all CUDA calls to use ofi wrapper functions | Mike Wilkins |
| [STL-76972](https://cornelisnetworks.atlassian.net/browse/STL-76972) | Libfabric | Restore debugging #ifdef | Bob Cernohous |
| [STL-76965](https://cornelisnetworks.atlassian.net/browse/STL-76965) | Libfabric | Dual plane multiple tx and ibv context | Archana Venkatesha |
| [STL-77075](https://cornelisnetworks.atlassian.net/browse/STL-77075) | Libfabric | SLES compilation fix | Archana Venkatesha |
| [STL-76966](https://cornelisnetworks.atlassian.net/browse/STL-76966) | Libfabric | Dual plane addressing, plane selection and shm | Archana Venkatesha |
| [STL-63325](https://cornelisnetworks.atlassian.net/browse/STL-63325) | Libfabric | Remove #if 0 dead code | Mike Wilkins |
"""

    # Parse and format the document
    lines = content.split('\n')
    out_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Format Release Info
        if line.startswith('# Release Information'):
            out_lines.append('# Release Information')
            i += 1
            if i < len(lines) and lines[i].startswith('----'):
                i += 1
            continue
            
        if line.startswith('## Summary of Changes'):
            out_lines.append(bug_table)
            out_lines.append('')
            out_lines.append('## Summary of Changes (Grouped)')
            i += 1
            if i < len(lines) and lines[i].startswith('----'):
                i += 1
            continue
            
        if line.startswith('## Full Commit Details'):
            out_lines.append('## Full Commit Details (Raw Log)')
            i += 1
            if i < len(lines) and lines[i].startswith('----'):
                i += 1
            continue
            
        # Format Group Headers (###)
        group_match = re.match(r'^###\s+(.+)$', line)
        if group_match and not line.startswith('### Commit:'):
            out_lines.append(f"### {group_match.group(1)}")
            i += 1
            if i < len(lines) and lines[i].startswith('----'):
                i += 1
            continue
            
        # Format Commit Details
        if line.startswith('### Commit:'):
            out_lines.append(line)
            i += 1
            # Skip the '----' line if present
            # We want to keep the metadata lines
            while i < len(lines) and not lines[i].startswith('---'):
                out_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].startswith('---'):
                i += 1 # skip separator
            out_lines.append('') # Add blank line before commit msg
            continue
            
        # Remove trailing dashed lines at end of commits
        if re.match(r'^-{20,}$', line):
            i += 1
            continue
            
        out_lines.append(line)
        i += 1

    try:
        with open(output_file, 'w') as f:
            f.write('\n'.join(out_lines))
        print(f"Successfully wrote {output_file}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
