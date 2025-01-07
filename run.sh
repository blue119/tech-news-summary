#!/usr/bin/env bash                                                                    
                                           
TOPDIR="$(dirname "$(readlink -f "$0")")"                                                                                                                                     
echo 'TOPDIR: ' $TOPDIR                                                                
cd ${TOPDIR}

poetry run python main.py
