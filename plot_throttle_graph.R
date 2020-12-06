setwd("~/Documents/Video-conference-evaluation")
library(dplyr)
library(ggplot2)
library(grid)
library(gridExtra)
###########################
path = "results/"
files = c('Zoom-throttle.csv', 'Teams-throttle.csv', 'Discord-throttle.csv')
###########################

for (i in 1:3) {
  file <- files[[i]]
  
  data <- read.csv(paste(path, files[[i]], sep=''))[1:599,]
  
  data <- data %>% mutate(cpu_usage = cpu_usage * 10)
  data <- data %>% mutate(bandwidth = bandwidth_calc / 1000) #bandwidth in kbytes
  data <- data %>% mutate(bandwidth_limit = bandwidth_limit / 1000) #bandwidth in kbytes
  data <- data %>% mutate(avg_packet_len = avg_packet_len  / 2.5) #bandwidth in kbytes
  data <- transform(data, bandwidth_limit = ifelse(bandwidth_limit == 0, NA, bandwidth_limit))
  
  coef <- 250
  
  p <- ggplot(data, aes(X)) +
    geom_smooth(aes(y=avg_packet_len, colour="Average packet size[kbytes]")) +
    geom_smooth(aes(y=packet_count, colour="Number of Packets")) + 
    geom_smooth(aes(y=cpu_usage, colour="Number of CPU cores used")) + 
    geom_line(aes(y=bandwidth_limit, colour="Bandwidth Limit"), linetype="dashed") + 
    scale_y_continuous(name = "Number of Packets; Bandwidth Limit", 
                       sec.axis = sec_axis(~./coef, name="Number of CPU cores; Avg packet size[KBytes]")
    ) +
    
    theme(axis.line.y.left = element_line(color = "black"), 
          axis.ticks.y.left = element_line(color = "black"),
          axis.text.y.left = element_text(color = "black"), 
          axis.title.y.left = element_text(color = "purple")
    ) + 
    theme(axis.line.y.right = element_line(color = "black"), 
          axis.ticks.y.right = element_line(color = "black"),
          axis.text.y.right = element_text(color = "black"), 
          axis.title.y.right = element_text(color = "blue")
    ) +
    scale_color_manual(name="Metric",values=c("blue", "red", "chartreuse4", "burlywood4")) +
    guides(colour = guide_legend(override.aes = list(linetype = 1))) +
    scale_x_continuous("Time(s)", breaks = seq(0, 600, 60))
  
  g <- ggplotGrob(p)
  g[[1]][[13]]$children[[1]]$label <- c("Number of Packets;",  " Bandwidth Limit")
  g[[1]][[13]]$children[[1]]$gp$col <- c("burlywood4", "red")
  g[[1]][[13]]$children[[1]]$gp$fontsize <- c(13,13)
  g[[1]][[13]]$children[[1]]$hjust <- c(1, -.02)
  g[[1]][[13]]$children[[1]]$y <- unit(c(0.5, 0.5), "npc")
  g[[1]][[14]]$children[[1]]$label <- c("Number of CPU cores;",  " Avg packet size[KBytes]")
  g[[1]][[14]]$children[[1]]$gp$col <- c("chartreuse4", "blue")
  g[[1]][[14]]$children[[1]]$gp$fontsize <- c(13,13)
  g[[1]][[14]]$children[[1]]$hjust <- c(1, -.02)
  g[[1]][[14]]$children[[1]]$y <- unit(c(0.5, 0.5), "npc")
  
  ggsave(paste(gsub('.csv','',files[[i]]),".pdf", sep=''), g)
}


