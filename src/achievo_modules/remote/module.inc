<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

//TODO: sistemare i permessi... una volta capiti...
    class mod_remote extends atkModule
    {
        function getNodes()
        {
          registerNode("remote.timereg",array("admin","add","edit","delete","lock","unlock", "any_user", "any_project"));
        }
        function getDependencies($mode)
        {
            return array("timestats");
        }
        function getMenuItems()
        {
          $this->menuitem("remote",
                          dispatch_url("remote.whoami", "admin"),
                          "main",true,370);
        }
    }
?>
