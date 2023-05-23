#!/bin/bash  
# Change into the directory of this script
#-------------------------------------------------------------------------------


for TEX_FILE in *.tex
do
	[ -f "${TEX_FILE:?}" ] && {
		rm -rf \
			"_minted-${TEX_FILE%.tex}" \
			"${TEX_FILE%.tex}.aux" \
			"${TEX_FILE%.tex}.log" \
			"${TEX_FILE%.tex}.out" \
			"${TEX_FILE%.tex}.toc" \
			"${TEX_FILE%.tex}.pyg" \
			"${TEX_FILE%.tex}.pdf" \
		|| { echo "ERROR" ; exit 1 ; }
	}
done

exit 0

