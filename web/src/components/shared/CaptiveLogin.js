import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button
} from '@chakra-ui/react'

import { useAuth0 } from '@auth0/auth0-react';

export const CaptiveLogin = (props) => {
  const { loginWithRedirect } = useAuth0();  
  return (
    <Modal isOpen={props.disclosure.isOpen} onClose={props.disclosure.onClose}>
      <ModalOverlay bg='none'
        backdropFilter='auto'
        backdropInvert='10%'
        backdropBlur='10px'/>
      <ModalContent>
        <ModalHeader>Login Required</ModalHeader><ModalCloseButton />
        <ModalBody>
          You must be logged in to perform this function.
        </ModalBody>
        <ModalFooter>
          <Button variant='ghost' colorScheme='red' mr={3} onClick={props.disclosure.onClose}>
            Cancel
          </Button>
          <Button colorScheme={"blue"} onClick={() => loginWithRedirect()} aria-label={`Log In`}>Log In</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};