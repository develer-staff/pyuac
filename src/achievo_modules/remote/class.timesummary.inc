<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

useattrib("atkdateattribute");

function str_number_format($var, $digits)
{
    if (is_numeric($var))
        return number_format($var, $digits, ",", ".");
    else
        return $var;
}

//Supporto per la colorazione alternata delle righe
$_flipflop = true;
function flipflop()
{
    global $_flipflop;
    $_flipflop = !$_flipflop;
    return $_flipflop;
}

class timesummary extends atkNode
{
    function timesummary()
    {
        $this->atkNode("timesummary");
    }

    function get_timesummary()
    {
        global $g_user;
        $userid = $g_user["id"];

        $db = &atkGetDb();

        /* Accetta una data in ingresso oppure imposta l'intervallo all'ultimo mese appena concluso*/
        $last_month_start  = mktime(0, 0, 0, date("m")-1, 1, date("Y"));
        $last_month_end = mktime(0, 0, 0, date("m"), 0, date("Y"));
        $date_start = $this->m_postvars['date_start'];
        $date_end = $this->m_postvars['date_end'];
        if ($date_start == "")
            $date_start = date("Y-m-d", $last_month_start);
        else
            $date_start = sprintf("%04d",$date_start["year"])."-".sprintf("%02d",$date_start["month"])."-".sprintf("%02d",$date_start["day"]);
        if ($date_end == "")
            $date_end = date("Y-m-d", $last_month_end);
        else
            $date_end = sprintf("%04d",$date_end["year"])."-".sprintf("%02d",$date_end["month"])."-".sprintf("%02d",$date_end["day"]);

        /* Accetta un testo con due colonne:
            username euro/ora
        */
        $euro_ora_text = $this->m_postvars['euro_ora_text'];
        $euro_ora_array = array();
        foreach (explode("\n", $euro_ora_text) as $line)
        {
            $line = explode(" ", $line);
            $euro_ora_array[$line[0]] = (real) $line[1];
        }
        atkdebug("euro_ora_array: ".var_export($euro_ora_array, 1));

        $select = "
                SELECT
                    person.userid,
                    project.name AS prj,
                    sum(hours.time)/60.0 as ore
                FROM hours
                    JOIN person ON hours.userid = person.id
                    JOIN phase ON hours.phaseid = phase.id
                    JOIN activity ON hours.activityid = activity.id
                    JOIN project ON phase.projectid = project.id";
        $filter = "
                WHERE
                    activitydate >= '$date_start' AND
                    activitydate <= '$date_end'";
        if (!$this->allowed("any_user")) $filter.= " AND hours.userid ='$userid' ";
        $groupby = "
                GROUP BY lower(person.userid), lower(prj)
                ORDER BY lower(person.userid), lower(prj)";

        $sql = $select . $filter . $groupby;

        return array("date_start" => $date_start,
                     "date_end" => $date_end,
                     "euro_ora_array" => $euro_ora_array,
                     "rows" => $db->getRows($sql));
    }

    function action_search()
    {
        atkdebug("timesummary Action search");

        $results = $this->get_timesummary();
        echo make_xml("timesummary", "$date_start<=D<=$date_end", $results['rows'], $bodykey="remark");
        exit;
    }

    function action_report()
    {
        $ui = &$this->getUi();
        $page = &$this->getPage();
        $this->addStyle("style.css");
        $content = '<form action="dispatch.php" method="get" name="entryform">';
        $content .= session_form();

        $results = $this->get_timesummary();
        $title = "Timereport: ".$results["date_start"]." - ".$results["date_end"];

        $startdateatt = new atkDateAttribute("date_start","F d Y","d F Y", 0, $results["date_start"], AF_OBLIGATORY);
        $enddateatt = new atkDateAttribute("date_end","F d Y","d F Y", 0, $results["date_end"], AF_OBLIGATORY);

        $content .= "Da ".$startdateatt->edit()." a ".$enddateatt->edit();
        $content .= "<h2>$title</h2>";

        // Tabella ore lavorate per progetto
        $content .= "<table border='1'>\n";
        $content .= "<tr><th>User Id</th><th>Progetto</th><th>Ore</th><th>Euro</th></tr>\n";
        $progetti = array();
        $persone = array();
        foreach ($results['rows'] as $key => $r)
        {
            if (!array_key_exists($r['prj'], $progetti)) $progetti[$r['prj']] = array("ore" => 0.0, "euro" => 0.0);
            if (!array_key_exists($r['userid'], $persone)) $persone[$r['userid']] = array("ore" => 0.0, "euro" => 0.0, "euro_ora" => 0.0);
            $progetti[$r['prj']]['ore'] += $r['ore'];
            $persone[$r['userid']]['ore'] += $r['ore'];

            atkdebug("Euro ora loop: ".var_export($r, 1)." incr ore prj:".var_export($progetti[$r['prj']], 1).", user:".var_export($persone[$r['userid']], 1));

            if (array_key_exists($r['userid'], $results['euro_ora_array']))
            {
                $r['euro'] = $r['ore'] * $results['euro_ora_array'][$r['userid']];
                $persone[$r['userid']]['euro_ora'] = $results['euro_ora_array'][$r['userid']];
            }
            else
            {
                $r['euro'] = "Manca euro/h";
                $persone[$r['userid']]['euro_ora'] = "Manca euro/h";
            }

            if (is_numeric($progetti[$r['prj']]['euro']) and is_numeric($r['euro']))
                $progetti[$r['prj']]['euro'] += $r['euro'];
            else
                $progetti[$r['prj']]['euro'] = "Manca euro/h";
            if (is_numeric($persone[$r['userid']]['euro']) and is_numeric($r['euro']))
                $persone[$r['userid']]['euro'] += $r['euro'];
            else
                $persone[$r['userid']]['euro'] = "Manca euro/h";

            if (flipflop())
                $content .= "<tr>";
            else
                $content .= "<tr style='background: #DDDDC0'>";
            $content .= "<td>".$r['userid']."</td><td>".$r['prj']."</td><td align='right'>".str_number_format($r['ore'], 2)."</td><td align='right'>".str_number_format($r['euro'], 2)."</td>";
            $content .= "</tr>\n";
        }
        $content .= "</table>";

        // Tabella ore per progetto / ore per persona
        $content .= "<table><tr><td>";
            // Tabella ore per progetto
            $content .= "<table border='1'><tr><th>Totale progetto</th><th>Ore</th><th>Euro</th></tr>";
            uksort($progetti, "strcasecmp"); //Ordina per chiave, le persone sono già ordinate
            foreach ($progetti as $key => $prj)
            {
                if (flipflop())
                    $content .= "<tr>";
                else
                    $content .= "<tr style='background: #DDDDC0'>";
                $content .= "<th>$key</th><td align='right'>".str_number_format($prj['ore'], 2)."</td><td align='right'>".str_number_format($prj['euro'], 2)."</td>";
                $content .= "</tr>\n";
            }
            $content .= "</table>";
        $content .= "</td><td>";
            // Tabella ore per persona
            $content .= "<table border='1'><tr><th>Totale persona</th><th>ore</th><th>euro/ora</th><th>euro</th><th>IVA</th><th>Ivato</th></tr>";
            $totale_ore_develer = 0;
            foreach ($persone as $key => $pers)
            {
                if (flipflop())
                    $content .= "<tr>";
                else
                    $content .= "<tr style='background: #DDDDC0'>";
                $content .= "<th>$key</th>";
                $content .= "<td align='right'>".str_number_format($pers['ore'], 2)."</td>";
                $content .= "<td align='right'>".str_number_format($pers['euro_ora'], 2)."</td>";
                $content .= "<td align='right'>".str_number_format($pers['euro'], 2)."</td>";
                $content .= "<td align='right'>".str_number_format($pers['euro']*0.2, 2)."</td>";
                $content .= "<td align='right'>".str_number_format($pers['euro']*1.2, 2)."</td>";
                $content .= "</tr>\n";
                $totale_ore_develer += $pers['ore'];
            }
            $content .= "<th>Totale</th><td align='right'>".str_number_format($totale_ore_develer, 2)."</td>";
            $content .= "<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>\n";
            $content .= "</table>";
        $content .= "</td></tr></table>";

        $content .= '<input type="submit" value="'.atktext("refresh").'">';

        $content .= "<table><tr><td>Inserire: nome_utente euro/h</td></tr>\n";
        $content .= "<tr><td><textarea rows='5' cols='40' name='euro_ora_text'>".$this->m_postvars['euro_ora_text']."</textarea>";
        $content .= "</td></tr></table>\n";

        $content .= '<input type="submit" value="'.atktext("refresh").'">';
        $content .= '<input type="hidden" name="atknodetype" value="'.$this->atkNodeType().'">';
        $content .= '<input type="hidden" name="atkaction" value="report">';

        $content .= '</form>';
        $page->addContent($ui->renderBox(array("title"=>$title,"content"=>$content)));
    }
}
?>
