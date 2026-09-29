# 每个用户的端口不同以避免冲突，要与 openclaw/openclaw.json 中设置的端口一致
# setwd("~/dataai_with_jupyterlab_and_rstudio")
options(rsession_api_token = "XXXXXXXXXXXXXX")
options(rsession_api_port = 8226)                                                                                         
source("r-session-ai/r-session-api.R") 
# stopServer
# httpuv::stopServer(server)
# stopAllServers也可以
#httpuv::stopAllServers()

