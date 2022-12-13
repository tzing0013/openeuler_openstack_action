# openeuler_openstack_action
Github Action for openEuler OpenStack SIG

## 1. RPM检查
Action：packge_status_check.yaml

每日检查OBS上OpenStack SIG项目的RPM构建情况，如有构建失败的情况，会自动发邮件给维护人员

## 2. CI检查
Action：openstack_ci_check.yaml

每日检查OpenStack社区openEuler CI情况，发送最近5次结果给维护人员

## 3. PR检查
Action：openstack_pr_check.yaml

每日检查OpenStack SIG 未合入的PR， 发送结果给maintainer

## 4. 项目刷新
Action：refresh_openeuler_repo.yaml

刷新openEuler和OpenStack SIG所有项目列表，提交PR到gitee openstack仓库

## 5. 文档刷新
Action：refresh_openstack_doc.yaml

刷新OpenStack SIG官方文档，提交PR到gitee openstack仓库

## 6. 版本刷新
Action：refresh_openstack_release.yaml

刷新OpenStack组件版本信息，提交PR到gitee openstack仓库

![Alt](https://repobeats.axiom.co/api/embed/0e8418c8ec4e3ecf1a47a22e410e8e496f53812e.svg "Repobeats analytics image")
