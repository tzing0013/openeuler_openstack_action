import datetime
import json
import os

import markdown
import requests
import xmltodict
import yaml


BRANCHS = [
    'openEuler:20.03:LTS:SP2:oepkg:openstack:queens',
    'openEuler:20.03:LTS:SP2:oepkg:openstack:rocky',
    'openEuler:20.03:LTS:SP2:oepkg:openstack:common',
    'openEuler:20.03:LTS:SP3:oepkg:openstack:queens',
    'openEuler:20.03:LTS:SP3:oepkg:openstack:rocky',
    'openEuler:20.03:LTS:SP3:oepkg:openstack:common',
    'openEuler:20.03:LTS:SP3:Epol',
    'openEuler:21.03:Epol',
    'openEuler:21.09:Epol',
    'openEuler:22.03:LTS:Next:Epol:Multi-Version:OpenStack:Train',
    'openEuler:22.03:LTS:Next:Epol:Multi-Version:OpenStack:Wallaby',
    'openEuler:Epol',
]


OBS_PACKAGE_BUILD_RESULT_URL = 'https://build.openeuler.org/build/%(branch)s/_result'
OBS_PROJECT_URL = 'https://build.openeuler.org/package/show/%(branch)s/%(project)s'
PROJECT_MARKDOWN_FORMAT = '[%(project)s](%(url)s)'
GITEE_ISSUE_LIST_URL = 'https://gitee.com/api/v5/repos/openeuler/openstack/issues?state=open&labels=kind/obs-failed&sort=created&direction=desc&page=1&per_page=20'
GITEE_ISSUE_CREATE_URL = 'https://gitee.com/api/v5/repos/openeuler/issues'
GITEE_ISSUE_UPDATE_URL = 'https://gitee.com/api/v5/repos/openeuler/issues/%s'
SIG_PROJECT_URL = 'https://gitee.com/openeuler/community/raw/master/sig/sig-openstack/sig-info.yaml'
OBS_USER_NAME = os.environ.get('OBS_USER_NAME')
OBS_USER_PASSWORD = os.environ.get('OBS_USER_PASSWORD')
GITEE_USER_TOKEN = os.environ.get('GITEE_USER_TOKEN')


def get_openstack_sig_project():
    project_list = []
    sig_dict = yaml.safe_load(requests.get(SIG_PROJECT_URL, verify=False).content.decode())
    for item in sig_dict['repositories']:
        project_list.append(item['repo'].split('/')[-1])
    return project_list


# The result dict format will be like:
# {
#     'branch_name': {
#         'package_name': {
#             'x86_64': 'fail reason',
#             'aarch64': 'fail reason'
#         }
#     },
#     'branch_name': 'Success',
#     'branch_name': 'Unknown',
# }
def check_status():
    white_list = get_openstack_sig_project()
    branch_session = requests.session()
    branch_session.auth = (OBS_USER_NAME, OBS_USER_PASSWORD)
    result = {}
    for branch in BRANCHS:
        sub_res = {}
        res = branch_session.get(OBS_PACKAGE_BUILD_RESULT_URL % {'branch': branch}, verify=False)
        obs_result = xmltodict.parse(res.content.decode())['resultlist']['result']
        for each_arch in obs_result:
            if each_arch['@state'] == 'unknown':
                result[branch] = 'Unknown'
                break
            arch = each_arch['@arch']
            arch_result = each_arch['status']
            for package in arch_result:
                package_name = package['@package']
                package_status = package['@code']
                if ('oepkg' in branch or 'Multi' in branch or package_name in white_list) and package_status in ['unresolvable', 'failed', 'broken']:
                    project_key = PROJECT_MARKDOWN_FORMAT % {'project': package_name, 'url': OBS_PROJECT_URL % {'branch': branch, 'project': package_name}}
                    if not sub_res.get(project_key):
                        sub_res[project_key] = {}
                    sub_res[project_key][arch] = package.get('details', 'build failed')
        else:
            if sub_res:
                result[branch] = sub_res
            else:
                result[branch] = 'Success'
    return result


def get_obs_issue():
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
    }
    issue_list = requests.get(GITEE_ISSUE_LIST_URL, headers=headers).content.decode()
    issue_list = json.loads(issue_list)
    if issue_list:
        return issue_list[0]['number']
    else:
        return None


# def update_issue(issue_number, result_str):
#     headers = {
#         'Content-Type': 'application/json;charset=UTF-8',
#     }
#     body = {
#         "access_token": GITEE_USER_TOKEN,
#         "repo": "openstack",
#         "body": result_str,
#     }
#     response = requests.patch(GITEE_ISSUE_UPDATE_URL % issue_number, headers=headers, params=body)
#     if response.status_code != 200:
#         raise Exception("Failed update gitee issue")

# def create_issue(result_str):
#     headers = {
#         'Content-Type': 'application/json;charset=UTF-8',
#     }
#     body = {
#         "access_token": GITEE_USER_TOKEN,
#         "repo": "openstack",
#         "title": "[CI] OBS Build Failed",
#         "body": result_str,
#         "labels": "kind/obs-failed",
#         "assignee": "huangtianhua",
#         "collaborators": "xiyuanwang"
#     }
#     response = requests.post(GITEE_ISSUE_CREATE_URL, headers=headers, params=body)
#     if response.status_code != 201:
#         raise Exception("Failed create gitee issue")


# def create_or_update_issue(result_str):
#     issue_number = get_obs_issue()
#     if issue_number:
#         update_issue(issue_number, result_str)
#     else:
#         create_issue(result_str)


def format_content(input_dict):
    output_attach = ""
    output_body = ""
    today = datetime.datetime.now()
    output_body += '# check date: %s-%s-%s\n\n' % (today.year, today.month, today.day)
    output_body += 'See the attached file for the failed branch\n\n'
    if input_dict:
        for branch, project_info in input_dict.items():
            if isinstance(project_info, str):
                output_body += '## %s\n\n' % branch
                output_body += '%s\n' % project_info
                continue
            output_attach += '## %s\n\n' % branch
            output_attach += '??? note "Detail"\n'
            for project_name, status in project_info.items():
                output_attach += '    %s:\n\n' % project_name
                if status.get('x86_64'):
                    output_attach += '        x86_64: %s\n' % status['x86_64']
                if status.get('aarch64'):
                    output_attach += '        aarch64: %s\n' % status['aarch64']
            output_attach += '\n'
    else:
        output_body += 'All package build success.'

    return output_attach, output_body


def main():
    result = check_status()
    result_str_attach, result_str_body= format_content(result)
    with open('result_attach.html', 'w') as f:
        html = markdown.markdown(result_str_attach, extensions=['pymdownx.details'])
        f.write(html)
    with open('result_body.html', 'w') as f:
        html = markdown.markdown(result_str_body, extensions=['pymdownx.details'])
        f.write(html)
main()
