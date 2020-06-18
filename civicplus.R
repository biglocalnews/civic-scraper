# """
# Author: Amy DiPierro
# Date modified: 2020-06-08
# Usage: Rscript civicplus.R
#
# This script scrapes new agendas and minutes from CivicPlus websites and
# downloads them into a local directory as .pdfs. Future versions should separate
# the scraping functionality from the downloading functionality.
#
# Inputs: GoogleSheet of CivicPlus URLs
# Outputs: .rds file of documents available to download
#          .pdfs of meeting agendas, minutes and some miscellaneous files.
# """

# Libraries
library(tidyverse)
library(rvest)
library(googlesheets4)
library(readr)
library(lubridate)

# Parameters

sheet_id <- "1SL8qU_1YQPesNyKWacTdT8UhtAKm6pHE7iR-mtpgNZA"
file_out <- here::here("data", "civicplus.rds")

# Code

# Read in the URLs and clean them up
cp_urls <-
  sheets_read(ss = sheet_id, sheet = "clean_list") %>%
  mutate(
    url = str_c("https://", url),
    doc_url = str_c(url, "/AgendaCenter")
  )

# Vector of dates in the next week for which we want to pull agendas and minutes
date_vector <-
  # Creates a vector of dates in the next week.
  seq(Sys.Date(), Sys.Date() + ddays(7), by = "1 day") %>%
  # Rearranges the order of the date
  map_chr(
    ~ str_remove_all(
      str_c(
        str_extract(., "-[:digit:]{2}-"), # Extracts the month
        str_extract(., "-[:digit:]{2}$"), # Extracts the day
        str_extract(., "[:digit:]{4}") # Extracts the year
      ),
      "-" # Removes dashes
    )
  )

# Function that scrapes each site
get_doc_links <- function(doc_url, url, ...) {
  tryCatch(
    doc_url %>%
      read_html() %>%
      html_nodes("#AgendaCenterContent .catAgendaRow a") %>%
      html_attr("href") %>%
      enframe(name = NULL) %>%
      mutate(
        url = str_c(url, value),
        value = na_if(value, ""),
        date = str_remove(str_extract(value, "_[:digit:]{8}"), "_"),
        title =
          str_replace(
            str_c(
              here::here("docs", "civicplus_docs"),
              "/", # Will need to modify this on PCs
              str_extract(url, "(?<=//).+(?=\\.)"),
              str_extract(value, "_[:digit:]{8}-[:digit:]+"),
              ".pdf"
            ),
            "\\.",
            "_"
          )
      ) %>%
      drop_na(value) %>%
      unique() %>%
      filter(
        str_detect(value, "true", negate = TRUE),
        str_detect(value, "Previous", negate = TRUE),
        str_detect(value, "https://", negate = TRUE),
        str_detect(value, "http://", negate = TRUE),
        str_detect(value, "www.", negate = TRUE),
        date %in% date_vector
      ),
    error = function(e) data.frame()
  )
}

# Grab URLs for all documents
doc_df <-
  map2_df(
    cp_urls$doc_url,
    cp_urls$url,
    ~ get_doc_links(.x, .y)
  )

# Write the URL dataframe into an .rds file
doc_df %>%
  write_rds(file_out)

# Download all of the files
map2(
  doc_df$url,
  doc_df$title,
  ~ tryCatch(
    download.file(.x, .y),
    error = function(e) data.frame()
  )
)
