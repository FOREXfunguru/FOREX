/* 
 * Workflow to run the tradebot on a set of pairs
 *
 * This workflow relies on Nextflow (see https://www.nextflow.io/tags/workflow.html)
 *
 * @author
 * Ernesto Lowy <ernesto.lowy@gmail.com>
 *
 */

// params defaults
params.help = false
//print usage
if (params.help) {
    log.info ''
    log.info 'Workflow to run the tradebot on a set of pairs'
    log.info '----------------------------------------------'
    log.info ''
    log.info 'Usage: '
    log.info '    nextflow run_trade_bot.nf --pairs VCF'
    log.info ''
    log.info 'Options:'
    log.info '	--help	Show this message and exit.'
    log.info '	--pairs AUD_USD,EUR_GBP    Comma-separated list of pairs to analyse.'
    log.info '  --timeframe H12, D  Timeframe to analyse.'
    log.info ''
    exit 1
}

log.info 'Starting the analysis.....'

pairs_list = Channel.from( params.pairs.split(',') )

process run_trade_bot {
    executor 'lsf   '
    maxForks 3
    cpus 1

    publishDir "results/", mode: 'copy', overwrite: true

    input:
    val pair from pairs_list

    output:
    file "${pair}_years2007_2008.per30.out.txt" into out_1
    file "${pair}_years2007_2008.per30.xlsx" into out_2
    file "${pair}_years2007_2008.pckl" into out_3
    file "${pair}_years2009_2010.per30.out.txt" into out_4
    file "${pair}_years2009_2010.per30.xlsx" into out_5
    file "${pair}_years2009_2010.pckl" into out_6
    file "${pair}_years2011_2012.per30.out.txt" into out_7
    file "${pair}_years2011_2012.per30.xlsx" into out_8
    file "${pair}_years2011_2012.pckl" into out_9
    file "${pair}_years2013_2014.per30.out.txt" into out_10
    file "${pair}_years2013_2014.per30.xlsx" into out_11
    file "${pair}_years2013_2014.pckl" into out_12
    file "${pair}_years2015_2017.per30.out.txt" into out_13
    file "${pair}_years2015_2017.per30.xlsx" into out_14
    file "${pair}_years2015_2017.pckl" into out_15
    file "${pair}_years2018_2020.per30.out.txt" into out_16
    file "${pair}_years2018_2020.per30.xlsx" into out_17
    file "${pair}_years2018_2020.pckl" into out_18

    """
    caffeinate -s -i python ${params.bin_folder}/main.py --pair ${pair} \
     --timeframe ${params.timeframe} --start '2007-01-01 22:00:00' \
      --end '2008-12-31 22:00:00' --settingf '${params.config}' \
      --url ${pair}_years2007_2008.per30.xlsx 2> ${pair}_years2007_2008.per30.out.txt
    caffeinate -s -i python ${params.bin_folder}/main.py --pair ${pair} \
     --timeframe ${params.timeframe} --start '2009-01-01 22:00:00' \
      --end '2010-12-31 22:00:00' --settingf '${params.config}' \
      --url ${pair}_years2009_2010.per30.xlsx 2> ${pair}_years2009_2010.per30.out.txt
    caffeinate -s -i python ${params.bin_folder}/main.py --pair ${pair} \
     --timeframe ${params.timeframe} --start '2011-01-01 22:00:00' \
      --end '2012-12-31 22:00:00' --settingf '${params.config}' \
      --url ${pair}_years2011_2012.per30.xlsx 2> ${pair}_years2011_2012.per30.out.txt
    caffeinate -s -i python ${params.bin_folder}/main.py --pair ${pair} \
     --timeframe ${params.timeframe} --start '2013-01-01 22:00:00' \
      --end '2014-12-31 22:00:00' --settingf '${params.config}' \
      --url ${pair}_years2013_2014.per30.xlsx 2> ${pair}_years2013_2014.per30.out.txt
    caffeinate -s -i python ${params.bin_folder}/main.py --pair ${pair} \
     --timeframe ${params.timeframe} --start '2015-01-01 22:00:00' \
      --end '2017-12-31 22:00:00' --settingf '${params.config}' \
      --url ${pair}_years2015_2017.per30.xlsx 2> ${pair}_years2015_2017.per30.out.txt
    caffeinate -s -i python ${params.bin_folder}/main.py --pair ${pair} \
     --timeframe ${params.timeframe} --start '2018-01-01 22:00:00' \
      --end '2020-02-20 22:00:00' --settingf '${params.config}' \
      --url ${pair}_years2018_2020.per30.xlsx 2> ${pair}_years2018_2020.per30.out.txt
    """
}
